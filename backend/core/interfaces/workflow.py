"""
Workflow Hook Interface

PURPOSE: Integration with external systems (PACS, RIS, LIS, HIS).
Hospitals use complex workflows:
- PACS (Picture Archiving and Communication System)
- RIS (Radiology Information System)
- LIS (Laboratory Information System)
- HIS (Hospital Information System)
- Worklist management (modality worklists)

VarunaPoC must integrate WITHOUT being coupled to specific vendors.

Pattern: Observer Pattern + Hook Pattern
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol


class WorkflowEventType(str, Enum):
    """
    Types of workflow events.
    Based on DICOM Modality Worklist and IHE workflows.
    """
    # Slide lifecycle
    SLIDE_RECEIVED = "slide_received"  # New slide arrived
    SLIDE_OPENED = "slide_opened"  # Pathologist opened slide
    SLIDE_CLOSED = "slide_closed"  # Pathologist closed slide
    SLIDE_ARCHIVED = "slide_archived"  # Slide moved to archive

    # Annotation events
    ANNOTATION_CREATED = "annotation_created"
    ANNOTATION_UPDATED = "annotation_updated"
    ANNOTATION_DELETED = "annotation_deleted"

    # ML events
    ML_INFERENCE_STARTED = "ml_inference_started"
    ML_INFERENCE_COMPLETED = "ml_inference_completed"
    ML_INFERENCE_FAILED = "ml_inference_failed"
    ML_FEEDBACK_SUBMITTED = "ml_feedback_submitted"  # Pathologist correction

    # Report events
    REPORT_CREATED = "report_created"
    REPORT_SIGNED = "report_signed"  # Pathologist signature
    REPORT_SENT_TO_RIS = "report_sent_to_ris"

    # PACS events
    PACS_QUERY_EXECUTED = "pacs_query_executed"
    PACS_RETRIEVE_COMPLETED = "pacs_retrieve_completed"
    PACS_STORE_COMPLETED = "pacs_store_completed"

    # Quality assurance
    QA_REVIEW_REQUESTED = "qa_review_requested"
    QA_REVIEW_COMPLETED = "qa_review_completed"


class WorkflowEvent:
    """
    Represents a workflow event with metadata.
    """
    def __init__(
        self,
        event_type: WorkflowEventType,
        slide_id: Optional[str] = None,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.event_type = event_type
        self.slide_id = slide_id
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}


class WorkflowHook(Protocol):
    """
    Protocol for workflow integrations.

    Implementations:
    - PACSWorkflowHook (DICOM integration)
    - RISWorkflowHook (Radiology system)
    - LISWorkflowHook (Laboratory system)
    - TelemisWorkflowHook (specific to Telemis PACS at CHU UCL)
    - NoOpWorkflowHook (no integration, for testing)

    Design Notes:
    - All methods MUST be async (non-blocking)
    - Hooks SHOULD NOT fail the main operation (fire-and-forget)
    - Hooks SHOULD log errors (for audit trail)
    - Hooks MAY be chained (multiple hooks for one event)
    """

    async def on_event(
        self,
        event: WorkflowEvent
    ) -> bool:
        """
        Handle workflow event.

        Args:
            event: WorkflowEvent object

        Returns:
            True if handled successfully, False otherwise

        Examples:
            >>> hook = PACSWorkflowHook(pacs_server="dicom.chu-ucl.be")
            >>> event = WorkflowEvent(
            ...     event_type=WorkflowEventType.SLIDE_OPENED,
            ...     slide_id="abc123",
            ...     user_id="pathologist1",
            ...     metadata={"patient_id": "12345", "accession_number": "A2025-001"}
            ... )
            >>> await hook.on_event(event)

        Behavior by Event Type:
            SLIDE_OPENED:
                - Update worklist (mark as "in progress")
                - Notify RIS (pathologist started review)
                - Log audit trail

            REPORT_SIGNED:
                - Send report to RIS
                - Update PACS (add report as secondary capture)
                - Notify referring physician

            ML_INFERENCE_COMPLETED:
                - Store results in PACS (structured report)
                - Update worklist (mark as "AI reviewed")
                - Trigger QA review if confidence low

        Notes:
            - MUST NOT block viewer operations
            - SHOULD retry on transient failures
            - SHOULD log all events (audit trail)
        """
        ...

    async def query_worklist(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Query DICOM modality worklist or equivalent.

        Args:
            filters: Optional filters (e.g., {"patient_id": "12345", "modality": "SM"})

        Returns:
            List of worklist items (dicts)

        Worklist Item Fields:
            - accession_number: str (unique identifier)
            - patient_id: str
            - patient_name: str
            - study_date: datetime
            - modality: str (e.g., "SM" for Slide Microscopy)
            - procedure_description: str
            - priority: str ("STAT", "HIGH", "ROUTINE")
            - status: str ("SCHEDULED", "IN_PROGRESS", "COMPLETED")

        Examples:
            >>> # Query today's worklist
            >>> worklist = await hook.query_worklist({
            ...     "study_date": datetime.now().date(),
            ...     "modality": "SM"
            ... })
            >>> for item in worklist:
            ...     print(f"{item['accession_number']}: {item['patient_name']}")

        Use Cases:
            - Display worklist in frontend (FolderBrowser)
            - Filter high-priority cases
            - Track workload (how many pending slides)

        DICOM Reference:
            - DICOM C-FIND with Modality Worklist SOP Class
            - Tag (0040,0100) Scheduled Procedure Step Sequence
        """
        ...

    async def update_worklist(
        self,
        accession_number: str,
        status: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Update worklist item status.

        Args:
            accession_number: Unique identifier
            status: New status ("IN_PROGRESS", "COMPLETED", etc.)
            metadata: Optional additional metadata

        Returns:
            True if updated successfully

        Status Transitions:
            SCHEDULED → IN_PROGRESS (pathologist opened slide)
            IN_PROGRESS → COMPLETED (report signed)
            COMPLETED → ARCHIVED (slide archived)

        Examples:
            >>> # Mark as in progress
            >>> await hook.update_worklist(
            ...     accession_number="A2025-001",
            ...     status="IN_PROGRESS",
            ...     metadata={"pathologist": "Dr. Smith"}
            ... )

            >>> # Mark as completed
            >>> await hook.update_worklist(
            ...     accession_number="A2025-001",
            ...     status="COMPLETED",
            ...     metadata={"report_id": "R2025-001", "diagnosis": "Benign"}
            ... )

        Use Cases:
            - Workflow tracking (which slides in progress)
            - Billing (track completed cases)
            - Quality metrics (turnaround time)
        """
        ...

    async def send_result(
        self,
        accession_number: str,
        result: Dict[str, Any]
    ) -> bool:
        """
        Send result to external system (RIS, LIS, HIS).

        Args:
            accession_number: Worklist item identifier
            result: Result data (structured report, annotations, etc.)

        Returns:
            True if sent successfully

        Result Formats:
            - HL7 ORU message (laboratory results)
            - DICOM Structured Report (SR)
            - FHIR DiagnosticReport (modern standard)
            - PDF report (legacy systems)

        Examples:
            >>> # Send structured report to RIS
            >>> result = {
            ...     "diagnosis": "Invasive ductal carcinoma",
            ...     "grade": "Grade 2",
            ...     "tumor_size_mm": 15.5,
            ...     "mitotic_count": 8,
            ...     "ml_confidence": 0.92,
            ...     "pathologist": "Dr. Smith",
            ...     "signed_at": datetime.now()
            ... }
            >>> await hook.send_result("A2025-001", result)

        DICOM SR Structure:
            - Document Title: "Pathology Report"
            - Observation Context: Patient, Study, Specimen
            - Content: Coded entries (SNOMED CT)
            - Signature: Digital signature (if required)

        Notes:
            - MUST validate result schema
            - SHOULD retry on network failures
            - MUST log transmission (audit trail)
        """
        ...

    async def get_patient_info(
        self,
        patient_id: str
    ) -> Optional[Dict]:
        """
        Retrieve patient information from HIS/RIS.

        Args:
            patient_id: Unique patient identifier

        Returns:
            Dict with patient info, or None if not found

        Patient Info Fields:
            - patient_id: str
            - patient_name: str
            - date_of_birth: datetime
            - gender: str ("M", "F", "O")
            - medical_record_number: str
            - referring_physician: str
            - insurance_info: Dict (optional)

        Examples:
            >>> patient = await hook.get_patient_info("12345")
            >>> print(f"Patient: {patient['patient_name']}")
            >>> print(f"DOB: {patient['date_of_birth']}")

        RGPD/HIPAA Notes:
            - MUST log access (audit trail)
            - MUST anonymize if not authorized
            - SHOULD use minimum necessary principle
            - MAY require user consent

        DICOM Reference:
            - DICOM C-FIND with Patient Root Query/Retrieve
            - Tags: (0010,0020) Patient ID, (0010,0010) Patient Name
        """
        ...

    async def validate_configuration(self) -> Dict[str, bool]:
        """
        Validate workflow integration configuration.

        Returns:
            Dict with validation results:
            - connection: bool (can connect to server)
            - authentication: bool (credentials valid)
            - permissions: bool (has required permissions)
            - version_compatible: bool (API version compatible)

        Use Cases:
            - Startup checks (fail fast if misconfigured)
            - Admin dashboard (show integration status)
            - Troubleshooting (diagnose connection issues)

        Examples:
            >>> status = await hook.validate_configuration()
            >>> if not status["connection"]:
            ...     print("ERROR: Cannot connect to PACS server")
            >>> if not status["permissions"]:
            ...     print("WARNING: Missing DICOM Store permission")
        """
        ...


class CompositeWorkflowHook(WorkflowHook, Protocol):
    """
    Composite hook that chains multiple hooks.

    Use Cases:
    - Send events to PACS AND RIS simultaneously
    - Log to file AND send to monitoring system
    - Broadcast to multiple hospital systems

    Pattern: Composite Pattern + Chain of Responsibility
    """

    def add_hook(self, hook: WorkflowHook) -> None:
        """
        Add hook to chain.

        Args:
            hook: WorkflowHook to add

        Examples:
            >>> composite = CompositeWorkflowHook()
            >>> composite.add_hook(PACSWorkflowHook())
            >>> composite.add_hook(RISWorkflowHook())
            >>> composite.add_hook(AuditLogHook())
            >>> # Now events sent to all 3 hooks
        """
        ...

    def remove_hook(self, hook: WorkflowHook) -> None:
        """
        Remove hook from chain.

        Args:
            hook: WorkflowHook to remove
        """
        ...

    def get_hooks(self) -> List[WorkflowHook]:
        """
        Get list of registered hooks.

        Returns:
            List of WorkflowHook instances
        """
        ...
