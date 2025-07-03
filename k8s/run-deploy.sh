#!/bin/bash

# SLN Kubernetes Deployment using Ansible
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
}

# Check if we're in the right directory
if [ ! -f "deploy-sln.yml" ]; then
    print_error "deploy-sln.yml not found. Please run this script from the k8s directory."
    exit 1
fi

print_header "SLN Kubernetes Deployment Setup"

# Check if ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    print_error "ansible-playbook is not installed. Please install Ansible first:"
    echo "  pip install ansible"
    exit 1
fi

# Check if kubectl is available and configured
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Test kubectl connectivity
if ! kubectl cluster-info &> /dev/null; then
    print_error "kubectl is not configured or cannot connect to cluster"
    print_warning "Make sure your kubeconfig is set up correctly"
    exit 1
fi

print_status "kubectl connectivity test passed"

# Check environment variables
CLOUDFLARE_API_TOKEN=""

# Parse command line arguments for tags and cloudflare token
TAGS=""
SKIP_TAGS=""
EXTRA_VARS=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --cloudflare-token)
            CLOUDFLARE_API_TOKEN="$2"
            shift 2
            ;;
        --tags)
            TAGS="--tags $2"
            shift 2
            ;;
        --skip-tags)
            SKIP_TAGS="--skip-tags $2"
            shift 2
            ;;
        --extra-vars)
            EXTRA_VARS="--extra-vars $2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --cloudflare-token TOKEN  Cloudflare API token"
            echo "  --tags TAGS              Run only tasks with these tags"
            echo "  --skip-tags TAGS         Skip tasks with these tags"
            echo "  --extra-vars VARS        Pass extra variables to Ansible"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "Available tags:"
            echo "  secrets              Setup secrets only"
            echo "  helm_repos           Add helm repositories only"
            echo "  cert_manager         Install cert-manager only"
            echo "  vault                Install HashiCorp Vault only"
            echo "  external_secrets     Install External Secrets Operator only"
            echo "  argocd               Install ArgoCD only"
            echo "  nginx_ingress        Install nginx-ingress only"
            echo "  memcached            Install memcached only"
            echo "  sln_app              Deploy SLN application only"
            echo "  ingress              Setup ingress and certificates only"
            echo "  monitoring           Setup monitoring stack only"
            echo "  certificates         Check certificate status only"
            echo ""
            echo "Environment variables:"
            echo "  CLOUDFLARE_API_TOKEN    Optional: Cloudflare API token (can use --cloudflare-token instead)"
            echo "  RELEASE_NAME           Optional: Helm release name (default: sln-prod)"
            echo "  STAGING_NAMESPACE      Optional: Kubernetes namespace (default: sln-prod)"
            echo ""
            echo "Examples:"
            echo "  $0 --cloudflare-token YOUR_TOKEN                   # Deploy everything with token"
            echo "  $0 --cloudflare-token YOUR_TOKEN --tags argocd     # Deploy only ArgoCD"
            echo "  $0 --cloudflare-token YOUR_TOKEN --tags secrets    # Deploy only secrets"
            echo "  $0 --skip-tags monitoring                          # Deploy everything except monitoring"
            echo ""
            echo "GitOps with ArgoCD:"
            echo "  After running with ArgoCD, deploy GitOps manifests:"
            echo "  cd ../manifests && ./deploy-manifests.sh"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if Cloudflare token is provided
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    print_warning "Cloudflare API token not provided via --cloudflare-token"
    read -p "Enter your Cloudflare API Token: " -s CLOUDFLARE_API_TOKEN
    echo
fi

if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    print_error "Cloudflare API token is required"
    exit 1
fi

# Set default values if not provided
export RELEASE_NAME=${RELEASE_NAME:-"sln-prod"}
export STAGING_NAMESPACE=${STAGING_NAMESPACE:-"sln-prod"}

print_status "Using release name: $RELEASE_NAME"
print_status "Using namespace: $STAGING_NAMESPACE"

# Install required Ansible collections
print_status "Installing required Ansible collections..."
ansible-galaxy collection install -r requirements.yml

# Run the Ansible playbook
print_header "Running Ansible Playbook"

ansible-playbook \
    -i inventory \
    deploy-sln.yml \
    --extra-vars "cloudflare_api_token=$CLOUDFLARE_API_TOKEN release_name=$RELEASE_NAME staging_namespace=$STAGING_NAMESPACE" \
    $TAGS \
    $SKIP_TAGS \
    $EXTRA_VARS \
    -v

print_header "Deployment Status Check"

# Show final status
print_status "Checking deployment status..."
echo ""

echo "Pods across all namespaces:"
kubectl get pods --all-namespaces | head -20

echo ""
echo "Services across all namespaces:"
kubectl get services --all-namespaces | head -10

echo ""
echo "Ingress resources:"
kubectl get ingress --all-namespaces

echo ""
print_status "Deployment completed! Check the output above for any issues."
print_status "To monitor certificate status: kubectl describe certificate spacelaunchnowme-tls"

# Check if ArgoCD was deployed and show login info
if kubectl get namespace argocd &>/dev/null && kubectl get secret argocd-initial-admin-secret -n argocd &>/dev/null; then
    echo ""
    print_header "ArgoCD Access Information"
    ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" 2>/dev/null | base64 -d || echo "Password not available")
    echo -e "${GREEN}ArgoCD URL:${NC} https://argo.spacelaunchnow.app"
    echo -e "${GREEN}Username:${NC} admin"
    echo -e "${GREEN}Password:${NC} $ARGOCD_PASSWORD"
    echo ""
    echo -e "${YELLOW}Next Steps for GitOps:${NC}"
    echo "1. Login to ArgoCD and change admin password"
    echo "2. Deploy GitOps applications:"
    echo "   cd ../manifests && ./deploy-manifests.sh"
    echo "3. Validate GitOps setup:"
    echo "   cd ../manifests && ./validate-manifests.sh"
fi
