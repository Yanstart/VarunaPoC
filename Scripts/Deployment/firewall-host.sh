#!/usr/bin/env bash
################################################################################
# VarunaPoC - Configuration Firewall Hôte (Serveur)
#
# Ce script configure automatiquement le firewall de l'hôte pour autoriser
# les connexions entrantes vers VarunaPoC.
#
# Usage:
#   ./firewall-host.sh [--remove]
#
# Options:
#   --remove    Supprimer les règles firewall VarunaPoC
#
# Ports ouverts:
#   - 80 (HTTP Frontend)
#   - 8000 (Backend API)
#   - 9090 (Prometheus)
#   - 3000 (Grafana)
#
# Compatibilité:
#   - Linux (ufw, iptables)
#   - Windows (via PowerShell avec bash)
################################################################################

set -e

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ports VarunaPoC
PORTS=(80 8000 9090 3000)
PORT_NAMES=("Frontend HTTP" "Backend API" "Prometheus" "Grafana")

print_header() {
    echo -e "${BLUE}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
    echo -e "${BLUE}Q${NC}  VarunaPoC - Configuration Firewall Hôte                           ${BLUE}Q${NC}"
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

# Détection OS
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

# Vérifier si script lancé avec privilèges
check_privileges() {
    if [[ "$OS" == "Linux" ]]; then
        if [[ $EUID -ne 0 ]]; then
            print_error "Ce script doit être exécuté avec sudo sur Linux"
            echo ""
            echo "Usage: sudo $0"
            exit 1
        fi
    elif [[ "$OS" == "Windows" ]]; then
        # Sur Windows via bash, vérifier si PowerShell a accès admin
        # On ne peut pas facilement vérifier, on va essayer et capturer l'erreur
        print_warning "Sur Windows, assurez-vous d'avoir ouvert PowerShell en Administrateur"
    fi
}

# Configuration firewall Linux (UFW)
configure_ufw() {
    print_info "Configuration via UFW (Ubuntu/Debian)..."
    echo ""

    # Vérifier si UFW est installé
    if ! command -v ufw &> /dev/null; then
        print_error "UFW n'est pas installé"
        print_info "Installation: sudo apt-get install ufw"
        return 1
    fi

    # Activer UFW si pas déjà fait
    if ! sudo ufw status | grep -q "Status: active"; then
        print_info "Activation de UFW..."
        sudo ufw --force enable
    fi

    # Ajouter règles pour chaque port
    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        NAME="${PORT_NAMES[$i]}"

        print_info "Autorisation port $PORT ($NAME)..."
        sudo ufw allow "$PORT/tcp" comment "VarunaPoC $NAME"
    done

    echo ""
    print_success "Règles UFW configurées"
    echo ""
    print_info "Status UFW:"
    sudo ufw status numbered
}

# Configuration firewall Linux (iptables)
configure_iptables() {
    print_info "Configuration via iptables..."
    echo ""

    # Vérifier si iptables est installé
    if ! command -v iptables &> /dev/null; then
        print_error "iptables n'est pas installé"
        return 1
    fi

    # Ajouter règles pour chaque port
    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        NAME="${PORT_NAMES[$i]}"

        print_info "Autorisation port $PORT ($NAME)..."
        sudo iptables -A INPUT -p tcp --dport "$PORT" -j ACCEPT -m comment --comment "VarunaPoC $NAME"
    done

    # Sauvegarder règles
    print_info "Sauvegarde des règles iptables..."

    if [[ -d "/etc/iptables" ]]; then
        sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
        print_success "Règles iptables sauvegardées"
    else
        print_warning "Répertoire /etc/iptables introuvable"
        print_info "Les règles sont actives mais ne survivront pas au redémarrage"
        print_info "Pour les rendre permanentes, installez: sudo apt-get install iptables-persistent"
    fi

    echo ""
    print_success "Règles iptables configurées"
}

# Configuration firewall Windows
configure_windows_firewall() {
    print_info "Configuration Firewall Windows..."
    echo ""

    print_warning "Ce script va exécuter des commandes PowerShell"
    print_warning "Assurez-vous que PowerShell est lancé en Administrateur"
    echo ""

    # Créer script PowerShell temporaire
    PS_SCRIPT=$(mktemp --suffix=.ps1)

    cat > "$PS_SCRIPT" << 'PSEOF'
# Script PowerShell pour configuration firewall VarunaPoC

$ports = @(
    @{Port=80; Name="Frontend HTTP"},
    @{Port=8000; Name="Backend API"},
    @{Port=9090; Name="Prometheus"},
    @{Port=3000; Name="Grafana"}
)

Write-Host "Configuration Firewall Windows Defender..." -ForegroundColor Cyan
Write-Host ""

foreach ($portConfig in $ports) {
    $port = $portConfig.Port
    $name = $portConfig.Name
    $ruleName = "VarunaPoC $name"

    Write-Host "[i] Création règle: $ruleName (port $port)" -ForegroundColor Blue

    try {
        New-NetFirewallRule -DisplayName $ruleName `
            -Direction Inbound `
            -LocalPort $port `
            -Protocol TCP `
            -Action Allow `
            -Profile Domain,Private `
            -ErrorAction Stop | Out-Null

        Write-Host "[] Règle créée avec succès" -ForegroundColor Green
    } catch {
        if ($_.Exception.Message -like "*already exists*") {
            Write-Host "[!] Règle existe déjà" -ForegroundColor Yellow
        } else {
            Write-Host "[] Erreur: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "[] Configuration terminée" -ForegroundColor Green
Write-Host ""
Write-Host "Règles VarunaPoC:" -ForegroundColor Cyan
Get-NetFirewallRule -DisplayName "VarunaPoC*" | Format-Table DisplayName, Enabled, Direction, Action -AutoSize
PSEOF

    # Exécuter script PowerShell
    if command -v powershell.exe &> /dev/null; then
        powershell.exe -ExecutionPolicy Bypass -File "$PS_SCRIPT"
    elif command -v pwsh &> /dev/null; then
        pwsh -ExecutionPolicy Bypass -File "$PS_SCRIPT"
    else
        print_error "PowerShell non trouvé"
        print_info "Veuillez exécuter manuellement les commandes suivantes dans PowerShell (Administrateur):"
        echo ""
        for i in "${!PORTS[@]}"; do
            PORT="${PORTS[$i]}"
            NAME="${PORT_NAMES[$i]}"
            echo "New-NetFirewallRule -DisplayName \"VarunaPoC $NAME\" -Direction Inbound -LocalPort $PORT -Protocol TCP -Action Allow"
        done
        rm -f "$PS_SCRIPT"
        return 1
    fi

    # Nettoyer
    rm -f "$PS_SCRIPT"

    echo ""
    print_success "Firewall Windows configuré"
}

# Suppression règles Linux (UFW)
remove_ufw() {
    print_info "Suppression des règles UFW..."
    echo ""

    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        NAME="${PORT_NAMES[$i]}"

        print_info "Suppression port $PORT ($NAME)..."
        sudo ufw delete allow "$PORT/tcp" 2>/dev/null || print_warning "Règle non trouvée"
    done

    echo ""
    print_success "Règles UFW supprimées"
}

# Suppression règles Linux (iptables)
remove_iptables() {
    print_info "Suppression des règles iptables..."
    echo ""

    for i in "${!PORTS[@]}"; do
        PORT="${PORTS[$i]}"
        NAME="${PORT_NAMES[$i]}"

        print_info "Suppression port $PORT ($NAME)..."
        sudo iptables -D INPUT -p tcp --dport "$PORT" -j ACCEPT 2>/dev/null || print_warning "Règle non trouvée"
    done

    # Sauvegarder
    if [[ -d "/etc/iptables" ]]; then
        sudo iptables-save | sudo tee /etc/iptables/rules.v4 > /dev/null
    fi

    echo ""
    print_success "Règles iptables supprimées"
}

# Suppression règles Windows
remove_windows_firewall() {
    print_info "Suppression des règles Windows..."
    echo ""

    PS_SCRIPT=$(mktemp --suffix=.ps1)

    cat > "$PS_SCRIPT" << 'PSEOF'
Write-Host "Suppression règles firewall VarunaPoC..." -ForegroundColor Cyan
Write-Host ""

$rules = Get-NetFirewallRule -DisplayName "VarunaPoC*"

if ($rules) {
    foreach ($rule in $rules) {
        Write-Host "[i] Suppression: $($rule.DisplayName)" -ForegroundColor Blue
        Remove-NetFirewallRule -DisplayName $rule.DisplayName
    }
    Write-Host ""
    Write-Host "[] Règles supprimées" -ForegroundColor Green
} else {
    Write-Host "[!] Aucune règle VarunaPoC trouvée" -ForegroundColor Yellow
}
PSEOF

    if command -v powershell.exe &> /dev/null; then
        powershell.exe -ExecutionPolicy Bypass -File "$PS_SCRIPT"
    elif command -v pwsh &> /dev/null; then
        pwsh -ExecutionPolicy Bypass -File "$PS_SCRIPT"
    fi

    rm -f "$PS_SCRIPT"

    echo ""
    print_success "Firewall Windows nettoyé"
}

# Main
main() {
    print_header

    # Détecter OS
    detect_os
    print_info "Système détecté: $OS"
    echo ""

    # Mode suppression
    if [[ "$1" == "--remove" ]]; then
        print_warning "Mode suppression des règles firewall"
        echo ""

        case "$OS" in
            Linux)
                check_privileges
                if command -v ufw &> /dev/null; then
                    remove_ufw
                elif command -v iptables &> /dev/null; then
                    remove_iptables
                else
                    print_error "Aucun firewall détecté (ufw/iptables)"
                    exit 1
                fi
                ;;
            Windows)
                remove_windows_firewall
                ;;
            *)
                print_error "OS non supporté: $OS"
                exit 1
                ;;
        esac

        exit 0
    fi

    # Mode configuration
    case "$OS" in
        Linux)
            check_privileges

            # Préférer UFW si disponible
            if command -v ufw &> /dev/null; then
                configure_ufw
            elif command -v iptables &> /dev/null; then
                configure_iptables
            else
                print_error "Aucun firewall détecté (ufw/iptables)"
                print_info "Installez UFW: sudo apt-get install ufw"
                exit 1
            fi
            ;;

        Windows)
            configure_windows_firewall
            ;;

        Mac)
            print_error "macOS n'est pas supporté pour ce script"
            print_info "Utilisez les Préférences Système > Sécurité > Pare-feu"
            exit 1
            ;;

        *)
            print_error "OS non supporté: $OS"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}TPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPW${NC}"
    echo -e "${GREEN}Q${NC}  Configuration firewall terminée avec succès!                       ${GREEN}Q${NC}"
    echo -e "${GREEN}ZPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP]${NC}"
    echo ""
    print_info "Ports ouverts:"
    for i in "${!PORTS[@]}"; do
        echo "  - ${PORTS[$i]} (${PORT_NAMES[$i]})"
    done
    echo ""
    print_info "Pour supprimer les règles: $0 --remove"
    echo ""
}

# Exécuter
main "$@"
