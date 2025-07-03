#!/bin/bash
# 🚀 ArgoCD All-in-One Setup Script
# Deploys ArgoCD and configures CI/CD integration for SpaceLaunchNow

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGOCD_NAMESPACE="argocd"
ARGOCD_VALUES="$SCRIPT_DIR/values.yaml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Show help message
show_help() {
    echo "ArgoCD All-in-One Setup Script for SpaceLaunchNow"
    echo ""
    echo "This script deploys ArgoCD and sets up CI/CD integration tokens."
    echo ""
    echo "Usage:"
    echo "  $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --cicd-only         Setup CI/CD integration only (ArgoCD must be deployed)"
    echo "  --deploy-only       Deploy ArgoCD only, skip CI/CD setup"
    echo "  --help, -h          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Full setup: Deploy ArgoCD + Configure CI/CD"
    echo "  $0 --cicd-only      # Setup CI/CD integration only"
    echo "  $0 --deploy-only    # Deploy ArgoCD only"
    echo ""
    echo "Prerequisites:"
    echo "  - kubectl configured for target cluster"
    echo "  - helm installed (for deployment)"
    echo "  - Cluster admin permissions"
    echo "  - cert-manager installed (for TLS certificates)"
    echo ""
    exit 0
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check cluster connectivity
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites met"
}

# Check deployment prerequisites
check_deploy_prerequisites() {
    # Check helm (only needed for deployment)
    if ! command -v helm &> /dev/null; then
        log_error "helm is not installed (required for deployment)"
        exit 1
    fi
    
    # Check values file exists
    if [ ! -f "$ARGOCD_VALUES" ]; then
        log_error "ArgoCD values file not found: $ARGOCD_VALUES"
        exit 1
    fi
}

# Install ArgoCD CLI if not present
install_argocd_cli() {
    if ! command -v argocd &> /dev/null; then
        log_info "Installing ArgoCD CLI..."
        curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
        sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
        rm argocd-linux-amd64
        log_success "ArgoCD CLI installed"
    else
        log_success "ArgoCD CLI already installed"
    fi
}

# Deploy ArgoCD using Helm
deploy_argocd() {
    log_header "🏗️ Deploying ArgoCD"
    
    check_deploy_prerequisites
    
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
    
    log_success "ArgoCD deployed successfully"
}

# Wait for ArgoCD to be ready
wait_for_argocd() {
    log_info "Waiting for ArgoCD to be ready..."
    
    # Wait for deployment to be ready
    kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n "$ARGOCD_NAMESPACE"
    
    # Wait for admin secret to be created
    local max_wait=60
    local waited=0
    
    while [ $waited -lt $max_wait ]; do
        if kubectl get secret argocd-initial-admin-secret -n "$ARGOCD_NAMESPACE" &>/dev/null; then
            log_success "ArgoCD is ready"
            return 0
        fi
        sleep 5
        waited=$((waited + 5))
    done
    
    log_error "Timeout waiting for ArgoCD admin secret"
    return 1
}

# Setup CI/CD integration
setup_cicd_integration() {
    log_header "🤖 Setting up CI/CD Integration"
    
    install_argocd_cli
    
    # Check if ArgoCD is deployed
    if ! kubectl get namespace "$ARGOCD_NAMESPACE" &> /dev/null; then
        log_error "ArgoCD namespace not found. Run with deployment first."
        exit 1
    fi
    
    # Check if ArgoCD server is running
    if ! kubectl get deployment argocd-server -n "$ARGOCD_NAMESPACE" &> /dev/null; then
        log_error "ArgoCD server deployment not found"
        exit 1
    fi
    
    # Get ArgoCD admin password
    log_info "Retrieving ArgoCD admin password..."
    if ! ADMIN_PASSWORD=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d 2>/dev/null); then
        log_error "Failed to retrieve admin password"
        exit 1
    fi
    log_success "Admin password retrieved"
    
    # Login to ArgoCD
    log_info "Logging into ArgoCD..."
    if argocd login argo.spacelaunchnow.app --username admin --password "$ADMIN_PASSWORD" --insecure --grpc-web; then
        log_success "Successfully logged into ArgoCD"
    else
        log_error "Failed to login to ArgoCD. Check if argo.spacelaunchnow.app is accessible"
        exit 1
    fi
    
    # Generate CI/CD token
    log_info "Generating CI/CD token (1 year expiration)..."
    if TOKEN=$(argocd account generate-token --account admin --expires-in 8760h --grpc-web); then
        log_success "Token generated successfully"
        
        echo ""
        log_warning "IMPORTANT: Add this token to your GitHub repository secrets:"
        echo -e "${YELLOW}Secret Name: ${GREEN}ARGOCD_TOKEN${NC}"
        echo -e "${YELLOW}Secret Value:${NC}"
        echo ""
        echo -e "${GREEN}$TOKEN${NC}"
        echo ""
        echo -e "${YELLOW}To add the secret:${NC}"
        echo "1. Go to your GitHub repository"
        echo "2. Settings → Secrets and variables → Actions"
        echo "3. Click 'New repository secret'"
        echo "4. Name: ARGOCD_TOKEN"
        echo "5. Value: [paste the token above]"
        echo ""
    else
        log_error "Failed to generate token"
        exit 1
    fi
    
    # Test token access (using auth-token method)
    log_info "Testing token access..."
    if argocd login argo.spacelaunchnow.app --auth-token "$TOKEN" --insecure --grpc-web; then
        log_success "Token access verified"
        
        # List applications to verify permissions
        log_info "Available applications:"
        argocd app list --grpc-web || log_warning "No applications found (this is normal for new installations)"
    else
        log_error "Token access failed"
        exit 1
    fi
}

# Show completion info
show_completion_info() {
    log_header "🎉 Setup Complete!"
    
    echo -e "${GREEN}✅ ArgoCD available at: https://argo.spacelaunchnow.app${NC}"
    echo ""
    
    # Login credentials
    echo -e "${BLUE}🔑 Login Credentials:${NC}"
    echo -e "   URL: https://argo.spacelaunchnow.app"
    echo -e "   Username: admin"
    
    if ADMIN_PASSWORD=$(kubectl -n "$ARGOCD_NAMESPACE" get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d 2>/dev/null); then
        echo -e "   Password: $ADMIN_PASSWORD"
        echo ""
        log_warning "IMPORTANT: Save this password! Change it after first login."
    else
        echo -e "   Password: Run this command to get it:"
        echo -e "   kubectl -n $ARGOCD_NAMESPACE get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
    fi
    
    echo ""
    echo -e "${BLUE}📖 Next Steps:${NC}"
    echo "1. Add the ARGOCD_TOKEN to your GitHub repository secrets"
    echo "2. Update your GitHub Actions workflows to use ArgoCD CLI"
    echo "3. Test a deployment using the new workflows"
    echo ""
    echo -e "${BLUE}� Documentation:${NC}"
    echo "- CI/CD Integration Guide: ./CICD_INTEGRATION.md"
    echo "- Rollback Guide: ../.github/ROLLBACK_GUIDE.md"
    echo "- Main CI/CD Docs: ../.github/CICD_README.md"
    echo ""
    echo -e "${BLUE}�️ Useful Commands:${NC}"
    echo "  # Check ArgoCD status"
    echo "  kubectl get pods -n $ARGOCD_NAMESPACE"
    echo ""
    echo "  # Check applications"
    echo "  kubectl get applications -n $ARGOCD_NAMESPACE"
    echo ""
    echo "  # ArgoCD CLI login"
    echo "  argocd login argo.spacelaunchnow.app"
}

# Main execution
main() {
    local deploy_argocd=true
    local setup_cicd=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cicd-only)
                deploy_argocd=false
                shift
                ;;
            --deploy-only)
                setup_cicd=false
                shift
                ;;
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
    
    log_header "🚀 ArgoCD All-in-One Setup"
    
    check_prerequisites
    
    if [ "$deploy_argocd" = true ]; then
        deploy_argocd
        wait_for_argocd
    fi
    
    if [ "$setup_cicd" = true ]; then
        setup_cicd_integration
    fi
    
    show_completion_info
}

# Run main function with all arguments
main "$@"
