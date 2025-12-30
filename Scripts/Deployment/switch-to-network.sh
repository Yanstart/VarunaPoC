#!/usr/bin/env bash
################################################################################
# Switch VarunaPoC from Phase 1 (localhost) to Phase 2.1 (network)
#
# Usage:
#   ./switch-to-network.sh <HOST_IP> [HOST_NAME]
#
# Examples:
#   ./switch-to-network.sh 192.168.1.100 varun-p-01
#   ./switch-to-network.sh 10.0.0.50
#
# What this script does:
# 1. Validates inputs (IP address format, optional hostname)
# 2. Updates backend/.env.phase2.1 (API URLs, CORS origins)
# 3. Updates frontend/.env.phase2.1 (API URL)
# 4. Updates docker-compose.phase2.1.yml (volumes)
# 5. Creates backup of original files
# 6. Displays summary of changes
#
# Prerequisites:
# - Phase 1 must be stopped (docker-compose down)
# - .env.phase1 files must exist
#
# Note: This script DOES NOT start Phase 2.1. After running this:
#   ./Scripts/Deployment/deploy-phase2.1.sh
################################################################################

set -euo pipefail

# ============================================================================
# Configuration
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_ENV="$PROJECT_ROOT/backend/.env.phase2.1"
FRONTEND_ENV="$PROJECT_ROOT/frontend/.env.phase2.1"
DOCKER_COMPOSE="$PROJECT_ROOT/docker-compose.phase2.1.yml"

# ============================================================================
# Colors for output
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Helper functions
# ============================================================================

print_header() {
    echo -e "${BLUE}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
    echo -e "${BLUE}Q${NC}  VarunaPoC - Switch to Network Mode (Phase 1 ’ Phase 2.1)          ${BLUE}Q${NC}"
    echo -e "${BLUE}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# ============================================================================
# Validation functions
# ============================================================================

validate_ip() {
    local ip="$1"

    # IP address regex (basic validation)
    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        # Validate each octet
        IFS='.' read -ra OCTETS <<< "$ip"
        for octet in "${OCTETS[@]}"; do
            if ((octet > 255)); then
                return 1
            fi
        done
        return 0
    else
        return 1
    fi
}

validate_hostname() {
    local hostname="$1"

    # Hostname regex (basic validation)
    if [[ $hostname =~ ^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?$ ]]; then
        return 0
    else
        return 1
    fi
}

# ============================================================================
# Backup functions
# ============================================================================

create_backup() {
    local file="$1"
    local backup="${file}.backup.$(date +%Y%m%d_%H%M%S)"

    if [[ -f "$file" ]]; then
        cp "$file" "$backup"
        print_success "Backup created: $backup"
        return 0
    else
        print_warning "File does not exist, skipping backup: $file"
        return 1
    fi
}

# ============================================================================
# Update functions
# ============================================================================

update_backend_env() {
    local host_ip="$1"
    local host_name="${2:-$host_ip}"

    print_info "Updating backend/.env.phase2.1..."

    # Create backup
    create_backup "$BACKEND_ENV"

    # Update API_BASE_URL
    sed -i.tmp "s|API_BASE_URL=http://[^:]*|API_BASE_URL=http://$host_name|g" "$BACKEND_ENV"

    # Update FRONTEND_URL
    sed -i.tmp "s|FRONTEND_URL=http://[^[:space:]]*|FRONTEND_URL=http://$host_name|g" "$BACKEND_ENV"

    # Update CORS_ORIGINS
    sed -i.tmp "s|CORS_ORIGINS=http://[^,]*|CORS_ORIGINS=http://$host_name|g" "$BACKEND_ENV"

    # Clean up temporary file
    rm -f "${BACKEND_ENV}.tmp"

    print_success "Backend environment updated"
}

update_frontend_env() {
    local host_ip="$1"
    local host_name="${2:-$host_ip}"

    print_info "Updating frontend/.env.phase2.1..."

    # Create backup
    create_backup "$FRONTEND_ENV"

    # Update VITE_API_URL
    sed -i.tmp "s|VITE_API_URL=http://[^:]*|VITE_API_URL=http://$host_name|g" "$FRONTEND_ENV"

    # Clean up temporary file
    rm -f "${FRONTEND_ENV}.tmp"

    print_success "Frontend environment updated"
}

update_docker_compose() {
    local host_ip="$1"
    local host_name="${2:-$host_ip}"

    print_info "Updating docker-compose.phase2.1.yml..."

    # Create backup
    create_backup "$DOCKER_COMPOSE"

    # Update build args in docker-compose
    sed -i.tmp "s|VITE_API_URL=http://[^:]*|VITE_API_URL=http://$host_name|g" "$DOCKER_COMPOSE"

    # Clean up temporary file
    rm -f "${DOCKER_COMPOSE}.tmp"

    print_success "Docker Compose configuration updated"
}

# ============================================================================
# Summary functions
# ============================================================================

display_summary() {
    local host_ip="$1"
    local host_name="${2:-$host_ip}"

    echo ""
    echo -e "${GREEN}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
    echo -e "${GREEN}Q${NC}  Configuration Updated Successfully!                                 ${GREEN}Q${NC}"
    echo -e "${GREEN}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
    echo ""

    echo -e "${BLUE}Network Configuration:${NC}"
    echo -e "  Host IP:       $host_ip"
    echo -e "  Host Name:     $host_name"
    echo ""

    echo -e "${BLUE}Updated Files:${NC}"
    echo -e "   backend/.env.phase2.1"
    echo -e "   frontend/.env.phase2.1"
    echo -e "   docker-compose.phase2.1.yml"
    echo ""

    echo -e "${BLUE}Next Steps:${NC}"
    echo -e "  1. Verify firewall allows ports 80, 8000, 9090"
    echo -e "  2. Configure DNS or hosts file for '$host_name'"
    echo -e "  3. Update slides volume mount in docker-compose.phase2.1.yml:"
    echo -e "     ${YELLOW}volumes:${NC}"
    echo -e "     ${YELLOW}  - C:\\Users\\junio\\Desktop\\CHU-UCL\\VarunaPoC\\Slides:/slides:ro${NC}"
    echo -e "  4. Deploy Phase 2.1:"
    echo -e "     ${GREEN}./Scripts/Deployment/deploy-phase2.1.sh${NC}"
    echo -e "  5. Test from client PC:"
    echo -e "     ${GREEN}curl http://$host_name/api/health${NC}"
    echo -e "     ${GREEN}Open browser ’ http://$host_name${NC}"
    echo -e "     ${GREEN}View metrics ’ http://$host_name:9090${NC}"
    echo ""
}

# ============================================================================
# Main script
# ============================================================================

main() {
    print_header

    # Check arguments
    if [[ $# -lt 1 ]]; then
        print_error "Missing required argument: HOST_IP"
        echo ""
        echo "Usage: $0 <HOST_IP> [HOST_NAME]"
        echo ""
        echo "Examples:"
        echo "  $0 192.168.1.100 varun-p-01"
        echo "  $0 10.0.0.50"
        exit 1
    fi

    local host_ip="$1"
    local host_name="${2:-$host_ip}"

    # Validate IP address
    print_info "Validating IP address: $host_ip"
    if ! validate_ip "$host_ip"; then
        print_error "Invalid IP address format: $host_ip"
        exit 1
    fi
    print_success "IP address valid"

    # Validate hostname (if provided)
    if [[ -n "$host_name" ]] && [[ "$host_name" != "$host_ip" ]]; then
        print_info "Validating hostname: $host_name"
        if ! validate_hostname "$host_name"; then
            print_error "Invalid hostname format: $host_name"
            exit 1
        fi
        print_success "Hostname valid"
    fi

    # Check if files exist
    print_info "Checking required files..."

    if [[ ! -f "$BACKEND_ENV" ]]; then
        print_error "Backend environment file not found: $BACKEND_ENV"
        exit 1
    fi

    if [[ ! -f "$FRONTEND_ENV" ]]; then
        print_error "Frontend environment file not found: $FRONTEND_ENV"
        exit 1
    fi

    if [[ ! -f "$DOCKER_COMPOSE" ]]; then
        print_error "Docker Compose file not found: $DOCKER_COMPOSE"
        exit 1
    fi

    print_success "All required files found"

    # Perform updates
    echo ""
    print_info "Updating configuration files..."

    update_backend_env "$host_ip" "$host_name"
    update_frontend_env "$host_ip" "$host_name"
    update_docker_compose "$host_ip" "$host_name"

    # Display summary
    display_summary "$host_ip" "$host_name"

    print_success "Switch to network mode completed!"
}

# Run main function
main "$@"
