#!/bin/bash

# Simple ArgoCD Deployment Script for SpaceLaunchNow
# Installs ArgoCD using Helm with values.yaml configuration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGOCD_NAMESPACE="argocd"
ARGOCD_VALUES="$SCRIPT_DIR/values.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo ""
    echo -e "${BLUE}===========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===========================================${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check helm
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check values file exists
    if [ ! -f "$ARGOCD_VALUES" ]; then
        log_error "ArgoCD values file not found: $ARGOCD_VALUES"
        exit 1
    fi
    
    log_success "Prerequisites met"
}

# Install ArgoCD using Helm
install_argocd() {
    log_info "Installing ArgoCD using Helm..."
    
    # Add ArgoCD Helm repository
    log_info "Adding ArgoCD Helm repository..."
    helm repo add argo https://argoproj.github.io/argo-helm
    helm repo update
    
    # Create namespace
    log_info "Creating namespace: $ARGOCD_NAMESPACE"
    kubectl create namespace "$ARGOCD_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Install or upgrade ArgoCD
    log_info "Installing ArgoCD with Helm..."
    helm upgrade --install argocd argo/argo-cd \
        --namespace "$ARGOCD_NAMESPACE" \
        --values "$ARGOCD_VALUES" \
        --wait \
        --timeout 15m
    
    log_success "ArgoCD installed successfully"
}

# Get admin password
get_admin_password() {
    local max_wait=60
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if kubectl get secret argocd-initial-admin-secret -n "$ARGOCD_NAMESPACE" &>/dev/null; then
            ADMIN_PASSWORD=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done
    
    return 1
}

# Display completion info
show_completion_info() {
    log_header "🎉 ArgoCD Deployment Complete!"
    
    echo -e "${GREEN}✅ ArgoCD installed in namespace: $ARGOCD_NAMESPACE${NC}"
    echo -e "${GREEN}✅ Available at: https://argo.spacelaunchnow.app${NC}"
    echo ""
    
    # Login credentials
    echo -e "${BLUE}🔑 Login Credentials:${NC}"
    echo -e "   URL: https://argo.spacelaunchnow.app"
    echo -e "   Username: admin"
    
    if get_admin_password; then
        echo -e "   Password: $ADMIN_PASSWORD"
        echo ""
        echo -e "${YELLOW}⚠️  IMPORTANT: Save this password! Change it after first login.${NC}"
    else
        echo -e "   Password: Run this command to get it:"
        echo -e "   kubectl -n $ARGOCD_NAMESPACE get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
    fi
    
    echo ""
    echo -e "${BLUE}️  Useful Commands:${NC}"
    echo "  # Check ArgoCD status"
    echo "  kubectl get pods -n $ARGOCD_NAMESPACE"
    echo ""
    echo "  # Check applications"
    echo "  kubectl get applications -n $ARGOCD_NAMESPACE"
    echo ""
    echo "  # Port-forward for local access"
    echo "  kubectl port-forward svc/argocd-server -n $ARGOCD_NAMESPACE 8080:443"
}

# Help message
show_help() {
    echo "Simple ArgoCD Deployment Script for SpaceLaunchNow"
    echo ""
    echo "This script installs ArgoCD using Helm with the values.yaml configuration."
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --apps-only         Deploy only applications (ArgoCD must be installed)"
    echo "  --skip-apps         Install ArgoCD without applications"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Install ArgoCD"
    echo ""
    echo "Prerequisites:"
    echo "  - kubectl configured for target cluster"
    echo "  - helm installed"
    echo "  - Cluster admin permissions"
    echo "  - cert-manager installed (for TLS certificates)"
    echo ""
    exit 0
}

# Main execution
main() {
    local deploy_apps=true
    local apps_only=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --help|-h)
                show_help
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    log_header "🚀 SpaceLaunchNow ArgoCD Deployment"
    
    check_prerequisites
    
    install_argocd
    
    show_completion_info
}

# Run main function with all arguments
main "$@"
