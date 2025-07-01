#!/bin/bash

# SpaceLaunchNow GitOps Deployment Script
# This script deploys the GitOps manifests structure to ArgoCD

set -e

ARGOCD_NAMESPACE="argocd"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFESTS_DIR="$SCRIPT_DIR"

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

# Check if ArgoCD is running
check_argocd() {
    log_info "Checking ArgoCD installation..."
    
    if ! kubectl get namespace "$ARGOCD_NAMESPACE" &> /dev/null; then
        log_error "ArgoCD namespace not found. Please install ArgoCD first."
        log_info "Run: cd ../k8s/argocd && ./install-argocd.sh"
        exit 1
    fi
    
    local server_ready=$(kubectl get deployment argocd-server -n "$ARGOCD_NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    if [ "$server_ready" -eq 0 ]; then
        log_error "ArgoCD server is not ready. Please wait for installation to complete."
        exit 1
    fi
    
    log_success "ArgoCD is running"
}

# Deploy ArgoCD project
deploy_project() {
    log_info "Deploying SpaceLaunchNow project..."
    
    if kubectl apply -f "$MANIFESTS_DIR/argocd/projects/spacelaunchnow.yaml"; then
        log_success "Project deployed successfully"
    else
        log_error "Failed to deploy project"
        exit 1
    fi
}

# Deploy infrastructure application
deploy_infrastructure() {
    log_info "Deploying infrastructure application..."
    
    if kubectl apply -f "$MANIFESTS_DIR/argocd/applications/sln-infrastructure.yaml"; then
        log_success "Infrastructure application deployed"
    else
        log_warning "Failed to deploy infrastructure application (may not be required)"
    fi
}

# Deploy App-of-Apps
deploy_app_of_apps() {
    log_info "Deploying App-of-Apps..."
    
    if kubectl apply -f "$MANIFESTS_DIR/argocd/app-of-apps.yaml"; then
        log_success "App-of-Apps deployed successfully"
        log_info "This will automatically create staging and production applications"
    else
        log_error "Failed to deploy App-of-Apps"
        exit 1
    fi
}

# Wait for applications to be created
wait_for_apps() {
    log_info "Waiting for applications to be created..."
    
    local apps=("sln-staging" "sln-production" "sln-infrastructure")
    local max_wait=60
    local waited=0
    
    for app in "${apps[@]}"; do
        waited=0
        while [ $waited -lt $max_wait ]; do
            if kubectl get application "$app" -n "$ARGOCD_NAMESPACE" &> /dev/null; then
                log_success "Application '$app' created"
                break
            fi
            sleep 5
            waited=$((waited + 5))
        done
        
        if [ $waited -ge $max_wait ]; then
            log_warning "Application '$app' not found after ${max_wait}s"
        fi
    done
}

# Check application health
check_app_health() {
    log_info "Checking application health..."
    
    local apps=("sln-staging" "sln-production" "sln-infrastructure" "sln-app-of-apps")
    
    for app in "${apps[@]}"; do
        if kubectl get application "$app" -n "$ARGOCD_NAMESPACE" &> /dev/null; then
            local health=$(kubectl get application "$app" -n "$ARGOCD_NAMESPACE" -o jsonpath='{.status.health.status}' 2>/dev/null || echo "Unknown")
            local sync=$(kubectl get application "$app" -n "$ARGOCD_NAMESPACE" -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "Unknown")
            
            echo "  📱 $app: Health=$health, Sync=$sync"
        else
            log_warning "Application '$app' not found"
        fi
    done
}

# Display next steps
show_next_steps() {
    echo ""
    log_info "🎉 GitOps Manifests Deployed!"
    log_info "=============================="
    echo ""
    log_info "📋 Next Steps:"
    echo "  1. 🌐 Access ArgoCD UI: https://argo.spacelaunchnow.app"
    echo "  2. 🔍 Review application status in ArgoCD UI"
    echo "  3. 🔄 For staging: Push to 'main' branch to trigger auto-sync"
    echo "  4. 🚀 For production: Use manual workflow and ArgoCD UI sync"
    echo ""
    log_info "🏗️ Manifest Structure:"
    echo "  📦 manifests/apps/staging/     - Staging environment config"
    echo "  📦 manifests/apps/production/  - Production environment config"
    echo "  🎛️  manifests/argocd/          - ArgoCD application configs"
    echo "  🔧 manifests/infrastructure/   - Infrastructure components"
    echo "  ⚓ manifests/helm/             - Helm chart"
    echo ""
    log_info "🛠️ Useful Commands:"
    echo "  # Validate deployment"
    echo "  ../k8s/argocd/validate-deployment.sh"
    echo ""
    echo "  # ArgoCD CLI login"
    echo "  argocd login argo.spacelaunchnow.app --insecure"
}

# Main execution
main() {
    echo ""
    log_info "🚀 SpaceLaunchNow GitOps Manifest Deployment"
    log_info "==========================================="
    echo ""
    
    check_argocd
    deploy_project
    deploy_infrastructure
    deploy_app_of_apps
    wait_for_apps
    check_app_health
    show_next_steps
}

# Help message
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "SpaceLaunchNow GitOps Manifest Deployment Script"
    echo ""
    echo "This script deploys the GitOps manifest structure to ArgoCD"
    echo ""
    echo "Usage:"
    echo "  $0                    # Deploy all manifests"
    echo "  $0 --help           # Show this help"
    echo ""
    echo "Prerequisites:"
    echo "  - ArgoCD must be installed"
    echo "  - kubectl must be configured for the target cluster"
    echo "  - Current user must have cluster-admin permissions"
    echo ""
    echo "Structure:"
    echo "  - Uses Kustomize for environment-specific configs"
    echo "  - Helm charts stored in manifests/helm/"
    echo "  - ArgoCD apps reference manifest paths"
    echo "  - Infrastructure managed separately"
    echo ""
    exit 0
fi

# Run main function
main "$@"
