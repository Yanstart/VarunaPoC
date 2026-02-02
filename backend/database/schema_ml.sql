-- schema_ml.sql
-- Database schema pour MLOps et apprentissage continu
-- Référence: docs/MLOPS_ARCHITECTURE.md Section 6

-- ============================================================================
-- EXTENSIONS POSTGRESQL
-- ============================================================================

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSONB functions
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- ============================================================================
-- SLIDES METADATA (avec tags ML)
-- ============================================================================

CREATE TABLE IF NOT EXISTS slides_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slide_id VARCHAR(255) UNIQUE NOT NULL,  -- MD5 hash du path
    slide_path TEXT NOT NULL,
    slide_name VARCHAR(500),
    format VARCHAR(100),
    vendor VARCHAR(100),

    -- Dimensions
    width INT,
    height INT,
    level_count INT,

    -- Tags ML (auto-détectés ou manuels)
    organ VARCHAR(100),
    stain VARCHAR(100),
    marker VARCHAR(100),
    task VARCHAR(100),
    tags_source VARCHAR(50),  -- 'dicom', 'properties', 'filename', 'ml_inference', 'manual'
    tags_confidence FLOAT CHECK (tags_confidence >= 0 AND tags_confidence <= 1),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_accessed TIMESTAMP,

    CONSTRAINT chk_tags_source CHECK (tags_source IN ('dicom', 'properties', 'filename', 'ml_inference', 'manual'))
);

-- Indexes pour performance
CREATE INDEX idx_slides_metadata_slide_id ON slides_metadata(slide_id);
CREATE INDEX idx_slides_metadata_organ ON slides_metadata(organ);
CREATE INDEX idx_slides_metadata_stain ON slides_metadata(stain);
CREATE INDEX idx_slides_metadata_marker ON slides_metadata(marker);
CREATE INDEX idx_slides_metadata_tags ON slides_metadata USING GIN ((to_tsvector('english', organ || ' ' || COALESCE(stain, '') || ' ' || COALESCE(marker, ''))));

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = NOW();
   RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_slides_metadata_updated_at BEFORE UPDATE ON slides_metadata
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ML PREDICTIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id VARCHAR(255) UNIQUE NOT NULL,

    -- Slide reference
    slide_id VARCHAR(255) NOT NULL,

    -- Model info
    model_id VARCHAR(255) NOT NULL,
    model_name VARCHAR(255),
    model_version VARCHAR(50),

    -- Prediction details
    prediction_class VARCHAR(255),
    prediction_proba JSONB,  -- {"class1": 0.85, "class2": 0.10, ...}
    confidence_score FLOAT CHECK (confidence_score >= 0 AND confidence_score <= 1),
    uncertainty_score FLOAT CHECK (uncertainty_score >= 0 AND uncertainty_score <= 1),

    -- Region of interest (si applicable)
    roi_coordinates JSONB,  -- {"x": 1000, "y": 2000, "width": 500, "height": 500}

    -- Explainability
    gradcam_path TEXT,  -- Chemin vers heatmap GradCAM
    shap_values JSONB,  -- SHAP values (si applicable)

    -- Metadata
    inference_time_ms FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Status tracking
    validation_status VARCHAR(50) DEFAULT 'pending',

    CONSTRAINT fk_slide FOREIGN KEY (slide_id) REFERENCES slides_metadata(slide_id) ON DELETE CASCADE,
    CONSTRAINT chk_validation_status CHECK (validation_status IN ('pending', 'approved', 'corrected', 'rejected'))
);

-- Indexes
CREATE INDEX idx_predictions_slide ON ml_predictions(slide_id);
CREATE INDEX idx_predictions_model ON ml_predictions(model_id);
CREATE INDEX idx_predictions_status ON ml_predictions(validation_status);
CREATE INDEX idx_predictions_timestamp ON ml_predictions(timestamp DESC);
CREATE INDEX idx_predictions_proba ON ml_predictions USING GIN (prediction_proba);

-- ============================================================================
-- ML FEEDBACK (pathologist corrections)
-- ============================================================================

CREATE TABLE IF NOT EXISTS ml_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slide_id VARCHAR(255) NOT NULL,
    prediction_id VARCHAR(255) NOT NULL,
    model_id VARCHAR(255) NOT NULL,
    model_version VARCHAR(50) NOT NULL,

    -- Feedback details
    action VARCHAR(50) NOT NULL,  -- 'approve', 'correct', 'reject', 'annotate'
    original_prediction JSONB,  -- Prédiction ML originale
    corrected_prediction JSONB,  -- Correction pathologiste (si action='correct')
    notes TEXT,

    -- Metadata
    pathologist_id VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'included_in_retraining', 'archived'

    -- Training inclusion tracking
    included_in_training_run VARCHAR(255),  -- MLflow run_id
    inclusion_timestamp TIMESTAMP,

    CONSTRAINT fk_slide_feedback FOREIGN KEY (slide_id) REFERENCES slides_metadata(slide_id) ON DELETE CASCADE,
    CONSTRAINT fk_prediction FOREIGN KEY (prediction_id) REFERENCES ml_predictions(prediction_id) ON DELETE CASCADE,
    CONSTRAINT chk_feedback_action CHECK (action IN ('approve', 'correct', 'reject', 'annotate')),
    CONSTRAINT chk_feedback_status CHECK (processing_status IN ('pending', 'included_in_retraining', 'archived'))
);

-- Indexes
CREATE INDEX idx_feedback_slide ON ml_feedback(slide_id);
CREATE INDEX idx_feedback_model ON ml_feedback(model_id);
CREATE INDEX idx_feedback_action ON ml_feedback(action);
CREATE INDEX idx_feedback_status ON ml_feedback(processing_status);
CREATE INDEX idx_feedback_timestamp ON ml_feedback(timestamp DESC);
CREATE INDEX idx_feedback_pathologist ON ml_feedback(pathologist_id);

-- ============================================================================
-- MODEL REGISTRY (sync avec MLflow)
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_registry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(255) UNIQUE NOT NULL,
    model_name VARCHAR(255) NOT NULL,

    -- Versioning
    version VARCHAR(50) NOT NULL,
    stage VARCHAR(50) DEFAULT 'staging',  -- 'staging', 'production', 'archived'

    -- Artifacts
    mlflow_run_id VARCHAR(255),
    artifact_uri TEXT,

    -- Performance metrics
    metrics JSONB,  -- {"accuracy": 0.94, "dice": 0.89, ...}

    -- Required tags (pour routing)
    required_tags JSONB,  -- {"organ": "prostate", "stain": "H&E"}

    -- Deployment
    deployment_date TIMESTAMP,
    traffic_percentage INT DEFAULT 0 CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),

    -- Metadata
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT chk_model_stage CHECK (stage IN ('staging', 'production', 'archived')),
    CONSTRAINT uq_model_version UNIQUE (model_id, version)
);

-- Indexes
CREATE INDEX idx_model_registry_model_id ON model_registry(model_id);
CREATE INDEX idx_model_registry_stage ON model_registry(stage);
CREATE INDEX idx_model_registry_tags ON model_registry USING GIN (required_tags);

-- ============================================================================
-- RETRAINING LOGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS retraining_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    model_id VARCHAR(255) NOT NULL,

    -- Trigger info
    trigger_type VARCHAR(50),  -- 'feedback_threshold', 'scheduled', 'manual', 'drift_detected'
    trigger_timestamp TIMESTAMP DEFAULT NOW(),

    -- Dataset info
    dataset_version VARCHAR(255),  -- DVC version hash
    dataset_size INT,
    feedback_count INT,

    -- Training info
    mlflow_run_id VARCHAR(255),
    training_duration_seconds INT,

    -- Results
    validation_metrics JSONB,
    comparison_with_production JSONB,

    -- Deployment
    deployment_status VARCHAR(50),  -- 'validated', 'deployed', 'failed', 'rollback'
    deployment_timestamp TIMESTAMP,

    -- Metadata
    notes TEXT,

    CONSTRAINT fk_model_retraining FOREIGN KEY (model_id) REFERENCES model_registry(model_id) ON DELETE CASCADE,
    CONSTRAINT chk_trigger_type CHECK (trigger_type IN ('feedback_threshold', 'scheduled', 'manual', 'drift_detected')),
    CONSTRAINT chk_deployment_status CHECK (deployment_status IN ('validated', 'deployed', 'failed', 'rollback'))
);

-- Indexes
CREATE INDEX idx_retraining_logs_model ON retraining_logs(model_id);
CREATE INDEX idx_retraining_logs_timestamp ON retraining_logs(trigger_timestamp DESC);
CREATE INDEX idx_retraining_logs_status ON retraining_logs(deployment_status);

-- ============================================================================
-- DRIFT MONITORING
-- ============================================================================

CREATE TABLE IF NOT EXISTS drift_monitoring (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    model_id VARCHAR(255) NOT NULL,

    -- Drift detection
    check_timestamp TIMESTAMP DEFAULT NOW(),
    drift_type VARCHAR(50),  -- 'data_drift', 'prediction_drift', 'performance_drift'

    -- Metrics
    drift_score FLOAT,  -- PSI, KS statistic, etc.
    drift_threshold FLOAT,
    drift_detected BOOLEAN,

    -- Details
    drift_details JSONB,  -- Détails par feature/classe

    -- Actions
    alert_sent BOOLEAN DEFAULT FALSE,
    retraining_triggered BOOLEAN DEFAULT FALSE,

    CONSTRAINT fk_model_drift FOREIGN KEY (model_id) REFERENCES model_registry(model_id) ON DELETE CASCADE,
    CONSTRAINT chk_drift_type CHECK (drift_type IN ('data_drift', 'prediction_drift', 'performance_drift'))
);

-- Indexes
CREATE INDEX idx_drift_model ON drift_monitoring(model_id);
CREATE INDEX idx_drift_timestamp ON drift_monitoring(check_timestamp DESC);
CREATE INDEX idx_drift_detected ON drift_monitoring(drift_detected);

-- ============================================================================
-- ACTIVE LEARNING QUEUE
-- ============================================================================

CREATE TABLE IF NOT EXISTS active_learning_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    slide_id VARCHAR(255) NOT NULL,
    prediction_id VARCHAR(255),

    -- Uncertainty metrics
    uncertainty_score FLOAT,
    entropy_score FLOAT,
    margin_score FLOAT,

    -- Prioritization
    priority_score FLOAT,  -- Combined metric
    sampling_method VARCHAR(100),  -- 'uncertainty', 'margin', 'entropy', 'query_by_committee'

    -- Status
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'assigned', 'completed', 'skipped'
    assigned_to VARCHAR(255),  -- Pathologist ID
    assigned_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT fk_slide_al FOREIGN KEY (slide_id) REFERENCES slides_metadata(slide_id) ON DELETE CASCADE,
    CONSTRAINT chk_al_status CHECK (status IN ('pending', 'assigned', 'completed', 'skipped'))
);

-- Indexes
CREATE INDEX idx_al_queue_status ON active_learning_queue(status);
CREATE INDEX idx_al_queue_priority ON active_learning_queue(priority_score DESC) WHERE status = 'pending';
CREATE INDEX idx_al_queue_assigned ON active_learning_queue(assigned_to) WHERE status = 'assigned';

-- ============================================================================
-- VIEWS UTILES
-- ============================================================================

-- Vue: Statistics par modèle
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT
    mr.model_id,
    mr.model_name,
    mr.version,
    mr.stage,
    COUNT(DISTINCT mp.id) as total_predictions,
    SUM(CASE WHEN mp.validation_status = 'approved' THEN 1 ELSE 0 END) as approvals,
    SUM(CASE WHEN mp.validation_status = 'corrected' THEN 1 ELSE 0 END) as corrections,
    SUM(CASE WHEN mp.validation_status = 'rejected' THEN 1 ELSE 0 END) as rejections,
    ROUND(100.0 * SUM(CASE WHEN mp.validation_status = 'approved' THEN 1 ELSE 0 END) /
          NULLIF(COUNT(DISTINCT mp.id), 0), 2) as approval_rate,
    AVG(mp.confidence_score) as avg_confidence,
    AVG(mp.uncertainty_score) as avg_uncertainty,
    AVG(mp.inference_time_ms) as avg_inference_time_ms
FROM model_registry mr
LEFT JOIN ml_predictions mp ON mr.model_id = mp.model_id
GROUP BY mr.model_id, mr.model_name, mr.version, mr.stage;

-- Vue: Pending feedback count par modèle
CREATE OR REPLACE VIEW pending_feedback_summary AS
SELECT
    model_id,
    model_version,
    COUNT(*) as pending_count,
    SUM(CASE WHEN action = 'correct' THEN 1 ELSE 0 END) as corrections_count,
    MAX(timestamp) as last_feedback_date,
    MIN(timestamp) as oldest_feedback_date
FROM ml_feedback
WHERE processing_status = 'pending'
GROUP BY model_id, model_version;

-- Vue: Active Learning priority queue
CREATE OR REPLACE VIEW active_learning_priority_queue AS
SELECT
    al.id,
    al.slide_id,
    sm.slide_name,
    sm.organ,
    sm.stain,
    sm.marker,
    al.uncertainty_score,
    al.priority_score,
    al.sampling_method,
    al.created_at
FROM active_learning_queue al
JOIN slides_metadata sm ON al.slide_id = sm.slide_id
WHERE al.status = 'pending'
ORDER BY al.priority_score DESC
LIMIT 100;

-- Vue: Recent drift alerts
CREATE OR REPLACE VIEW recent_drift_alerts AS
SELECT
    dm.model_id,
    mr.model_name,
    dm.drift_type,
    dm.drift_score,
    dm.drift_detected,
    dm.check_timestamp,
    dm.retraining_triggered
FROM drift_monitoring dm
JOIN model_registry mr ON dm.model_id = mr.model_id
WHERE dm.check_timestamp >= NOW() - INTERVAL '7 days'
  AND dm.drift_detected = TRUE
ORDER BY dm.check_timestamp DESC;

-- ============================================================================
-- FUNCTIONS UTILES
-- ============================================================================

-- Function: Calculate approval rate pour un modèle
CREATE OR REPLACE FUNCTION calculate_approval_rate(p_model_id VARCHAR(255))
RETURNS FLOAT AS $$
DECLARE
    total_count INT;
    approval_count INT;
BEGIN
    SELECT COUNT(*) INTO total_count
    FROM ml_predictions
    WHERE model_id = p_model_id AND validation_status IS NOT NULL;

    IF total_count = 0 THEN
        RETURN NULL;
    END IF;

    SELECT COUNT(*) INTO approval_count
    FROM ml_predictions
    WHERE model_id = p_model_id AND validation_status = 'approved';

    RETURN ROUND((approval_count::FLOAT / total_count::FLOAT) * 100, 2);
END;
$$ LANGUAGE plpgsql;

-- Function: Check if retraining needed
CREATE OR REPLACE FUNCTION should_trigger_retraining(
    p_model_id VARCHAR(255),
    p_feedback_threshold INT DEFAULT 100,
    p_approval_rate_threshold FLOAT DEFAULT 0.85,
    p_days_threshold INT DEFAULT 30
)
RETURNS BOOLEAN AS $$
DECLARE
    pending_feedback_count INT;
    current_approval_rate FLOAT;
    days_since_last_retraining INT;
BEGIN
    -- Check feedback count
    SELECT COUNT(*) INTO pending_feedback_count
    FROM ml_feedback
    WHERE model_id = p_model_id AND processing_status = 'pending';

    IF pending_feedback_count >= p_feedback_threshold THEN
        RETURN TRUE;
    END IF;

    -- Check approval rate
    current_approval_rate := calculate_approval_rate(p_model_id);
    IF current_approval_rate IS NOT NULL AND current_approval_rate < (p_approval_rate_threshold * 100) THEN
        RETURN TRUE;
    END IF;

    -- Check time elapsed
    SELECT EXTRACT(DAY FROM (NOW() - MAX(trigger_timestamp))) INTO days_since_last_retraining
    FROM retraining_logs
    WHERE model_id = p_model_id;

    IF days_since_last_retraining >= p_days_threshold THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA (for testing)
-- ============================================================================

-- Insert sample model (commented out - uncomment pour testing)
/*
INSERT INTO model_registry (model_id, model_name, version, stage, required_tags, metrics)
VALUES (
    'gleason_grading_v2',
    'Gleason Grading Model',
    '2.1.0',
    'production',
    '{"organ": "prostate", "stain": "H&E", "task": "grading"}',
    '{"accuracy": 0.94, "cohen_kappa": 0.89}'
);
*/

-- ============================================================================
-- PERMISSIONS (adjust selon environnement)
-- ============================================================================

-- Grant permissions to varuna_ml user (example)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO varuna_ml;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO varuna_ml;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO varuna_ml;
