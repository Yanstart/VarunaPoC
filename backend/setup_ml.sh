#!/bin/bash
# ML Integration Setup Script
# Installe et configure l'intégration Slideflow pour VarunaPoC
#
# Usage:
#   ./setup_ml.sh [--with-slideflow] [--with-mlops]
#
# Options:
#   --with-slideflow    Installe Slideflow (optionnel, ~2GB)
#   --with-mlops        Installe outils MLOps (MLflow, DVC, etc.)
#   --gpu               Configure pour GPU (CUDA)
#   --help              Affiche cette aide

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Options
INSTALL_SLIDEFLOW=false
INSTALL_MLOPS=false
GPU_SUPPORT=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-slideflow)
            INSTALL_SLIDEFLOW=true
            shift
            ;;
        --with-mlops)
            INSTALL_MLOPS=true
            shift
            ;;
        --gpu)
            GPU_SUPPORT=true
            shift
            ;;
        --help)
            head -n 14 "$0" | tail -n 11
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}VarunaPoC - ML Integration Setup${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}Error: Python $required_version or higher required (found $python_version)${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $python_version${NC}"
echo ""

# Install core dependencies
echo -e "${YELLOW}Installing core ML dependencies...${NC}"
pip install numpy>=1.24.0 \
            pydantic>=2.0.0 \
            pillow>=10.0.0 \
            matplotlib>=3.7.0 \
            scikit-learn>=1.3.0

echo -e "${GREEN}✓ Core dependencies installed${NC}"
echo ""

# Install Slideflow (optionnel)
if [ "$INSTALL_SLIDEFLOW" = true ]; then
    echo -e "${YELLOW}Installing Slideflow...${NC}"
    echo -e "${YELLOW}(This may take several minutes - ~2GB download)${NC}"

    if [ "$GPU_SUPPORT" = true ]; then
        # TensorFlow with GPU
        pip install tensorflow[and-cuda]==2.14.0
        pip install slideflow[tf]==2.2.0
        echo -e "${GREEN}✓ Slideflow installed with TensorFlow GPU support${NC}"
    else
        # TensorFlow CPU only
        pip install tensorflow==2.14.0
        pip install slideflow[tf]==2.2.0
        echo -e "${GREEN}✓ Slideflow installed with TensorFlow CPU${NC}"
    fi
    echo ""
else
    echo -e "${YELLOW}Skipping Slideflow installation (use MockProvider for testing)${NC}"
    echo -e "${YELLOW}To install later: pip install slideflow[tf]${NC}"
    echo ""
fi

# Install MLOps tools (optionnel)
if [ "$INSTALL_MLOPS" = true ]; then
    echo -e "${YELLOW}Installing MLOps tools...${NC}"
    pip install mlflow==2.9.0 \
                dvc==3.35.0 \
                boto3==1.34.0 \
                evidently==0.4.0
    echo -e "${GREEN}✓ MLOps tools installed (MLflow, DVC, Evidently)${NC}"
    echo ""
else
    echo -e "${YELLOW}Skipping MLOps tools${NC}"
    echo -e "${YELLOW}To install later: pip install mlflow dvc boto3 evidently${NC}"
    echo ""
fi

# Setup configuration
echo -e "${YELLOW}Setting up configuration...${NC}"

# Copy ml_routes.yaml if not exists
if [ ! -f "config/ml_routes.yaml" ]; then
    if [ -f "config/ml_routes.yaml.example" ]; then
        cp config/ml_routes.yaml.example config/ml_routes.yaml
        echo -e "${GREEN}✓ Created config/ml_routes.yaml from example${NC}"
    else
        echo -e "${RED}Warning: config/ml_routes.yaml.example not found${NC}"
    fi
else
    echo -e "${GREEN}✓ config/ml_routes.yaml already exists${NC}"
fi

# Update .env
if [ -f ".env" ]; then
    # Check if ML config already exists
    if grep -q "ML_ENABLED" .env; then
        echo -e "${GREEN}✓ ML configuration already in .env${NC}"
    else
        echo "" >> .env
        echo "# ML Configuration" >> .env
        echo "ML_ENABLED=true" >> .env

        if [ "$INSTALL_SLIDEFLOW" = true ]; then
            echo "ML_PROVIDER=slideflow" >> .env
        else
            echo "ML_PROVIDER=mock" >> .env
        fi

        if [ "$GPU_SUPPORT" = true ]; then
            echo "ML_DEVICE=cuda" >> .env
        else
            echo "ML_DEVICE=auto" >> .env
        fi

        echo "ML_ROUTES_CONFIG=config/ml_routes.yaml" >> .env
        echo "ML_MODEL_CACHE_DIR=/app/models" >> .env
        echo -e "${GREEN}✓ Added ML configuration to .env${NC}"
    fi
else
    echo -e "${RED}Warning: .env file not found${NC}"
    echo -e "${YELLOW}Creating .env with ML configuration...${NC}"
    cat > .env << EOF
# ML Configuration
ML_ENABLED=true
ML_PROVIDER=$([ "$INSTALL_SLIDEFLOW" = true ] && echo "slideflow" || echo "mock")
ML_DEVICE=$([ "$GPU_SUPPORT" = true ] && echo "cuda" || echo "auto")
ML_ROUTES_CONFIG=config/ml_routes.yaml
ML_MODEL_CACHE_DIR=/app/models
EOF
    echo -e "${GREEN}✓ Created .env with ML configuration${NC}"
fi
echo ""

# Run tests
echo -e "${YELLOW}Running ML integration tests...${NC}"
if pytest tests/test_ml_integration.py -v --tb=short; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${YELLOW}This is expected if Slideflow is not installed${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Configuration:"
echo -e "  - Provider: $([ "$INSTALL_SLIDEFLOW" = true ] && echo "Slideflow" || echo "Mock")"
echo -e "  - Device: $([ "$GPU_SUPPORT" = true ] && echo "GPU (CUDA)" || echo "CPU/Auto")"
echo -e "  - MLOps: $([ "$INSTALL_MLOPS" = true ] && echo "Yes" || echo "No")"
echo ""
echo -e "Next steps:"
echo -e "  1. Review config/ml_routes.yaml and customize models"
echo -e "  2. Start API: ${GREEN}uvicorn main:app --reload${NC}"
echo -e "  3. Visit API docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  4. Test ML endpoints: ${GREEN}curl http://localhost:8000/api/ml/health${NC}"
echo ""
echo -e "Documentation:"
echo -e "  - Full guide: ${GREEN}docs/ML_INTEGRATION.md${NC}"
echo -e "  - Quick start: ${GREEN}backend/services/ml/INTEGRATION_README.md${NC}"
echo ""
echo -e "${YELLOW}Note: If using MockProvider, ML features work without Slideflow!${NC}"
echo ""
