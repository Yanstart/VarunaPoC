#!/usr/bin/env bash
################################################################################
# VarunaPoC - Test Connectivité Client ’ Serveur
#
# Ce script teste la connectivité réseau entre un PC client et le serveur
# VarunaPoC (Phase 2.1).
#
# Usage:
#   ./test-connectivity.sh <SERVER_IP>
#
# Example:
#   ./test-connectivity.sh 192.168.1.100
#
# Tests effectués:
#   - Ping serveur
#   - Test ports: 80 (Frontend), 8000 (Backend), 9090 (Prometheus), 3000 (Grafana)
#   - Test HTTP endpoints (health checks)
#
# Compatibilité:
#   - Linux (natif)
#   - Windows (via bash/Git Bash)
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ports à tester
PORTS=(80 8000 9090 3000)
PORT_NAMES=("Frontend" "Backend API" "Prometheus" "Grafana")
PORT_URLS=("/" "/api/health" "/-/healthy" "/api/health")

print_header() {
    echo -e "${BLUE}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
    echo -e "${BLUE}Q${NC}  VarunaPoC - Test Connectivité Client ’ Serveur                    ${BLUE}Q${NC}"
    echo -e "${BLUE}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}[]${NC} $1"
}

print_error() {
    echo -e "${RED}[]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Détecter OS
detect_os() {
    case "$(uname -s)" in
        Linux*)
            OS="Linux"
            ;;
        Darwin*)
            OS="Mac"
            ;;
        CYGWIN*|MINGW*|MSYS*)
            OS="Windows"
            ;;
        *)
            OS="Unknown"
            ;;
    esac
}

# Valider IP
validate_ip() {
    local ip=$1

    if [[ $ip =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
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

# Test ping
test_ping() {
    local server=$1

    print_info "Test 1/3: Ping serveur..."

    if [[ "$OS" == "Windows" ]]; then
        # Windows ping format
        if ping -n 4 "$server" > /dev/null 2>&1; then
            print_success "Ping réussi"
            return 0
        else
            print_error "Ping échoué"
            return 1
        fi
    else
        # Linux/Mac ping format
        if ping -c 4 -W 2 "$server" > /dev/null 2>&1; then
            print_success "Ping réussi"
            return 0
        else
            print_error "Ping échoué"
            return 1
        fi
    fi
}

# Test port TCP
test_port() {
    local server=$1
    local port=$2
    local name=$3

    # Essayer différentes méthodes selon disponibilité

    # Méthode 1: nc (netcat)
    if command -v nc &> /dev/null; then
        if nc -z -w 2 "$server" "$port" 2>/dev/null; then
            print_success "Port $port ($name) accessible"
            return 0
        else
            print_error "Port $port ($name) inaccessible"
            return 1
        fi
    fi

    # Méthode 2: telnet
    if command -v telnet &> /dev/null; then
        if echo "quit" | telnet "$server" "$port" 2>/dev/null | grep -q "Connected"; then
            print_success "Port $port ($name) accessible"
            return 0
        else
            print_error "Port $port ($name) inaccessible"
            return 1
        fi
    fi

    # Méthode 3: curl (HTTP uniquement)
    if command -v curl &> /dev/null; then
        if curl -s --connect-timeout 2 "http://$server:$port" > /dev/null 2>&1; then
            print_success "Port $port ($name) accessible"
            return 0
        else
            print_error "Port $port ($name) inaccessible"
            return 1
        fi
    fi

    # Méthode 4: bash /dev/tcp (dernier recours)
    if timeout 2 bash -c "echo >/dev/tcp/$server/$port" 2>/dev/null; then
        print_success "Port $port ($name) accessible"
        return 0
    else
        print_error "Port $port ($name) inaccessible"
        return 1
    fi
}

# Test HTTP endpoint
test_http() {
    local server=$1
    local port=$2
    local path=$3
    local name=$4

    if ! command -v curl &> /dev/null; then
        print_warning "curl non disponible, skip test HTTP"
        return 2
    fi

    local url="http://$server:$port$path"

    if curl -s --connect-timeout 5 --max-time 10 "$url" > /dev/null 2>&1; then
        print_success "HTTP $name répondant"
        return 0
    else
        print_warning "HTTP $name ne répond pas (mais port ouvert)"
        return 1
    fi
}

# Tests complets
run_tests() {
    local server=$1
    local total_tests=0
    local passed_tests=0

    echo ""
    print_info "Serveur cible: $server"
    print_info "Système client: $OS"
    echo ""

    # Test 1: Ping
    echo -e "${BLUE}PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP${NC}"
    if test_ping "$server"; then
        ((passed_tests++))
    fi
    ((total_tests++))
    echo ""

    # Test 2: Ports TCP
    echo -e "${BLUE}PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP${NC}"
    print_info "Test 2/3: Ports TCP..."
    echo ""

    for i in "${!PORTS[@]}"; do
        if test_port "$server" "${PORTS[$i]}" "${PORT_NAMES[$i]}"; then
            ((passed_tests++))
        fi
        ((total_tests++))
    done

    echo ""

    # Test 3: Endpoints HTTP
    echo -e "${BLUE}PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP${NC}"
    print_info "Test 3/3: Endpoints HTTP..."
    echo ""

    for i in "${!PORTS[@]}"; do
        result=$(test_http "$server" "${PORTS[$i]}" "${PORT_URLS[$i]}" "${PORT_NAMES[$i]}")
        if [[ $? -eq 0 ]]; then
            ((passed_tests++))
        elif [[ $? -eq 2 ]]; then
            # curl non disponible, ne pas compter comme échec
            ((total_tests--))
        fi
        ((total_tests++))
    done

    echo ""

    # Résumé
    echo -e "${BLUE}PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP${NC}"
    echo ""

    if [[ $passed_tests -eq $total_tests ]]; then
        echo -e "${GREEN}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
        echo -e "${GREEN}Q${NC}   Tous les tests passés ($passed_tests/$total_tests)                              ${GREEN}Q${NC}"
        echo -e "${GREEN}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
        echo ""
        print_success "Le serveur VarunaPoC est accessible depuis ce client"
        echo ""
        print_info "URLs à tester dans le navigateur:"
        echo "  - Frontend:   http://$server"
        echo "  - Backend:    http://$server:8000/docs"
        echo "  - Prometheus: http://$server:9090"
        echo "  - Grafana:    http://$server:3000 (admin/varuna2024)"
        echo ""
        return 0
    else
        echo -e "${YELLOW}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
        echo -e "${YELLOW}Q${NC}  ! Tests partiellement réussis ($passed_tests/$total_tests)                        ${YELLOW}Q${NC}"
        echo -e "${YELLOW}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
        echo ""
        print_warning "Certains services ne sont pas accessibles"
        echo ""

        if [[ $passed_tests -eq 0 ]]; then
            print_error "Aucun service accessible - Problèmes possibles:"
            echo ""
            echo "1. Serveur VarunaPoC non démarré"
            echo "   ’ Vérifier: docker ps sur le serveur"
            echo ""
            echo "2. Firewall serveur bloque les connexions"
            echo "   ’ Exécuter: ./Scripts/Deployment/firewall-host.sh sur le serveur"
            echo ""
            echo "3. Problème réseau (routage, sous-réseau différent)"
            echo "   ’ Vérifier: IP correcte, même réseau local"
            echo ""
        else
            print_info "Dépannage des services inaccessibles:"
            echo ""
            echo "1. Vérifier conteneurs Docker:"
            echo "   docker ps --format 'table {{.Names}}\t{{.Status}}'"
            echo ""
            echo "2. Vérifier logs:"
            echo "   docker-compose -f docker-compose.phase2.1.yml logs [service]"
            echo ""
            echo "3. Vérifier firewall serveur:"
            echo "   ./Scripts/Deployment/firewall-host.sh"
            echo ""
        fi

        return 1
    fi
}

# Main
main() {
    print_header

    # Vérifier argument
    if [[ $# -ne 1 ]]; then
        print_error "Argument manquant: IP serveur"
        echo ""
        echo "Usage: $0 <SERVER_IP>"
        echo ""
        echo "Example:"
        echo "  $0 192.168.1.100"
        exit 1
    fi

    SERVER_IP=$1

    # Valider IP
    if ! validate_ip "$SERVER_IP"; then
        print_error "Adresse IP invalide: $SERVER_IP"
        exit 1
    fi

    # Détecter OS
    detect_os

    # Exécuter tests
    run_tests "$SERVER_IP"
    exit_code=$?

    echo ""
    exit $exit_code
}

# Exécuter
main "$@"
