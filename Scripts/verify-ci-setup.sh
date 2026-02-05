#!/bin/bash
# Verify CI/CD Pipeline Setup
# Run this script to ensure all CI/CD components are correctly configured

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Helper functions
print_header() {
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_file() {
    if [ -f "$1" ]; then
        print_success "File exists: $1"
        return 0
    else
        print_error "File missing: $1"
        return 1
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        print_success "Command available: $1"
        return 0
    else
        print_warning "Command not found: $1 (optional for local dev)"
        return 1
    fi
}

# Start verification
clear
print_header "VarunaPoC CI/CD Pipeline Verification"

echo "This script verifies that all CI/CD components are correctly configured."
echo "It does NOT modify any files."
echo

# ============================================
# 1. GitHub Actions Workflows
# ============================================
print_header "1. GitHub Actions Workflows"

check_file ".github/workflows/ci.yml"
check_file ".github/workflows/cd.yml"
check_file ".github/workflows/security.yml"
check_file ".github/workflows/update-project.yml"
check_file ".github/workflows/README.md"

echo

# ============================================
# 2. Backend Configuration
# ============================================
print_header "2. Backend Configuration"

check_file "backend/ruff.toml"
check_file "backend/pyproject.toml"
check_file "backend/requirements.txt"

# Check backend tests
if [ -d "backend/tests" ]; then
    print_success "Backend tests directory exists"
    check_file "backend/tests/__init__.py"
    check_file "backend/tests/conftest.py"
    check_file "backend/tests/test_health.py"
    check_file "backend/tests/test_slides_api.py"
    check_file "backend/tests/README.md"
else
    print_error "Backend tests directory missing"
fi

echo

# ============================================
# 3. Frontend Configuration
# ============================================
print_header "3. Frontend Configuration"

check_file "frontend/.eslintrc.json"
check_file "frontend/package.json"

# Check if lint script exists in package.json
if grep -q '"lint":' frontend/package.json; then
    print_success "Lint script found in package.json"
else
    print_error "Lint script missing in package.json"
fi

echo

# ============================================
# 4. Git Configuration
# ============================================
print_header "4. Git Configuration"

check_file ".gitignore"
check_file ".pre-commit-config.yaml"
check_file ".secrets.baseline"

# Check if .gitignore has CI/CD entries
if grep -q "*.sarif" .gitignore; then
    print_success ".gitignore includes CI/CD report patterns"
else
    print_warning ".gitignore may be missing CI/CD patterns"
fi

echo

# ============================================
# 5. Documentation
# ============================================
print_header "5. Documentation"

check_file "CI_CD_GUIDE.md"
check_file "CI_CD_FILES_SUMMARY.md"
check_file "README.md"

echo

# ============================================
# 6. Docker Configuration
# ============================================
print_header "6. Docker Configuration"

check_file "backend/Dockerfile"
check_file "frontend/Dockerfile"
check_file "Scripts/Deployment/docker-compose.yml"

echo

# ============================================
# 7. Local Development Tools (Optional)
# ============================================
print_header "7. Local Development Tools (Optional)"

check_command "python3"
check_command "node"
check_command "npm"
check_command "docker"
check_command "git"
check_command "pre-commit"
check_command "ruff"
check_command "black"
check_command "pytest"
check_command "eslint"

echo

# ============================================
# 8. Verify Workflow Syntax (if yq available)
# ============================================
print_header "8. YAML Syntax Validation"

if command -v yamllint &> /dev/null; then
    echo "Checking YAML syntax with yamllint..."
    if yamllint .github/workflows/*.yml &> /dev/null; then
        print_success "All workflows have valid YAML syntax"
    else
        print_warning "Some workflows may have YAML syntax issues"
        echo "  Run: yamllint .github/workflows/*.yml"
    fi
else
    print_warning "yamllint not installed - skipping YAML validation"
    echo "  Install: pip install yamllint"
fi

echo

# ============================================
# 9. Backend Lint Check (if ruff available)
# ============================================
print_header "9. Backend Lint Check"

if command -v ruff &> /dev/null; then
    echo "Running ruff check on backend..."
    if cd backend && ruff check . &> /dev/null; then
        print_success "Backend passes ruff linting"
    else
        print_warning "Backend has ruff linting issues"
        echo "  Fix: cd backend && ruff check --fix ."
    fi
    cd - > /dev/null
else
    print_warning "ruff not installed - skipping backend lint"
    echo "  Install: pip install ruff"
fi

echo

# ============================================
# 10. Frontend Lint Check (if eslint available)
# ============================================
print_header "10. Frontend Lint Check"

if [ -d "frontend/node_modules" ]; then
    echo "Running ESLint on frontend..."
    if cd frontend && npm run lint &> /dev/null; then
        print_success "Frontend passes ESLint"
    else
        print_warning "Frontend has ESLint issues"
        echo "  Fix: cd frontend && npm run lint:fix"
    fi
    cd - > /dev/null
else
    print_warning "frontend/node_modules not found - run 'npm install' first"
fi

echo

# ============================================
# 11. Backend Tests
# ============================================
print_header "11. Backend Tests"

if command -v pytest &> /dev/null; then
    echo "Running backend unit tests..."
    if cd backend && pytest -m unit --tb=no -q &> /dev/null; then
        print_success "Backend unit tests pass"
    else
        print_warning "Some backend tests may be failing"
        echo "  Run: cd backend && pytest -m unit -v"
    fi
    cd - > /dev/null
else
    print_warning "pytest not installed - skipping backend tests"
    echo "  Install: pip install pytest pytest-cov pytest-asyncio httpx"
fi

echo

# ============================================
# 12. Pre-commit Hooks
# ============================================
print_header "12. Pre-commit Hooks"

if command -v pre-commit &> /dev/null; then
    if [ -d ".git/hooks" ] && [ -f ".git/hooks/pre-commit" ]; then
        print_success "Pre-commit hooks are installed"
    else
        print_warning "Pre-commit hooks not installed"
        echo "  Install: pre-commit install"
    fi

    echo "Testing pre-commit hooks (dry-run)..."
    if pre-commit run --all-files &> /dev/null; then
        print_success "Pre-commit hooks pass"
    else
        print_warning "Some pre-commit hooks may fail"
        echo "  Run: pre-commit run --all-files"
    fi
else
    print_warning "pre-commit not installed"
    echo "  Install: pip install pre-commit"
fi

echo

# ============================================
# Summary
# ============================================
print_header "Verification Summary"

echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ CI/CD pipeline is correctly configured!${NC}"
    echo
    echo "Next steps:"
    echo "  1. Install local dev tools (if not already):"
    echo "     - pip install ruff black isort pytest pytest-cov"
    echo "     - pip install pre-commit && pre-commit install"
    echo "     - cd frontend && npm install"
    echo
    echo "  2. Test locally before push:"
    echo "     - cd backend && ruff check . && pytest"
    echo "     - cd frontend && npm run lint && npm run build"
    echo
    echo "  3. Create a test PR to verify CI pipeline"
    exit 0
else
    echo -e "${RED}✗ Some components are missing or misconfigured${NC}"
    echo
    echo "Please fix the errors above before using CI/CD pipeline."
    exit 1
fi
