#!/bin/bash

# GitOps Migration Validation Script
# Validates the complete GitOps setup for SpaceLaunchNow

set -e

SCRIPT_DIR=$(dirname "$0")
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 SpaceLaunchNow GitOps Migration Validation${NC}"
echo "=============================================="

# Counter for issues
ISSUES=0
WARNINGS=0

# Function to log different message types
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
    ((ISSUES++))
}

log_section() {
    echo
    echo -e "${CYAN}📋 $1${NC}"
    echo "$(echo "$1" | sed 's/./=/g')"
}

# Function to check file existence
check_file() {
    local file="$1"
    local description="$2"
    
    if [[ -f "$file" ]]; then
        log_success "$description exists: $file"
        return 0
    else
        log_error "$description missing: $file"
        return 1
    fi
}

# Function to check directory structure
check_directory() {
    local dir="$1"
    local description="$2"
    
    if [[ -d "$dir" ]]; then
        log_success "$description exists: $dir"
        return 0
    else
        log_error "$description missing: $dir"
        return 1
    fi
}

# Function to validate YAML syntax
validate_yaml() {
    local file="$1"
    
    # Try yq first, then fall back to python
    if yq eval '.' "$file" >/dev/null 2>&1; then
        return 0
    elif python3 -c "import yaml; yaml.safe_load_all(open('$file'))" >/dev/null 2>&1; then
        return 0
    else
        log_error "Invalid YAML syntax: $file"
        return 1
    fi
}

# Function to validate Helm chart
validate_helm_chart() {
    local chart_dir="$1"
    
    if ! helm lint "$chart_dir" >/dev/null 2>&1; then
        log_error "Helm chart validation failed: $chart_dir"
        return 1
    fi
    return 0
}

# Check prerequisites
log_section "Prerequisites Check"

# Check required tools
for tool in kubectl helm yq ansible-playbook; do
    if command -v "$tool" >/dev/null 2>&1; then
        log_success "$tool is installed"
    else
        log_error "$tool is not installed"
    fi
done

# Check Kubernetes connection
if kubectl cluster-info >/dev/null 2>&1; then
    log_success "Kubernetes cluster is accessible"
    CLUSTER_NAME=$(kubectl config current-context)
    log_info "Current context: $CLUSTER_NAME"
else
    log_warning "Kubernetes cluster is not accessible (this is OK for structure validation)"
fi

# Validate directory structure
log_section "Directory Structure Validation"

# Check main directories
check_directory "../manifests" "GitOps manifests directory"
check_directory "../manifests/apps" "Applications directory"
check_directory "../manifests/apps/staging" "Staging environment directory"
check_directory "../manifests/apps/production" "Production environment directory"
check_directory "../manifests/argocd" "ArgoCD configuration directory"
check_directory "../manifests/argocd/applications" "ArgoCD applications directory"
check_directory "../manifests/argocd/projects" "ArgoCD projects directory"
check_directory "../manifests/helm" "Helm charts directory"
check_directory "../manifests/helm/spacelaunchnow" "SpaceLaunchNow Helm chart directory"

# Validate core files
log_section "Core Configuration Files"

# Ansible playbook
check_file "deploy-sln.yml" "Main Ansible playbook"
check_file "argocd/values.yaml" "ArgoCD Helm values"

# ArgoCD configurations
check_file "../manifests/argocd/projects/spacelaunchnow.yaml" "ArgoCD project"
check_file "../manifests/argocd/app-of-apps.yaml" "App-of-Apps configuration"
check_file "../manifests/argocd/applications/sln-staging.yaml" "Staging application"
check_file "../manifests/argocd/applications/sln-production.yaml" "Production application"

# Environment configurations
check_file "../manifests/apps/staging/values-staging.yaml" "Staging Helm values"
check_file "../manifests/apps/production/values-prod.yaml" "Production Helm values"
check_file "../manifests/apps/staging/namespace.yaml" "Staging namespace definition"
check_file "../manifests/apps/production/namespace.yaml" "Production namespace definition"

# Helm chart
check_file "../manifests/helm/spacelaunchnow/Chart.yaml" "Helm Chart.yaml"

# GitHub Actions workflows
check_file "../.github/workflows/build-staging-argocd.yml" "Staging GitHub workflow"
check_file "../.github/workflows/build-production-argocd.yml" "Production GitHub workflow"

# Validate YAML syntax
log_section "YAML Syntax Validation"

yaml_files=(
    "deploy-sln.yml"
    "argocd/values.yaml"
    "../manifests/argocd/projects/spacelaunchnow.yaml"
    "../manifests/argocd/app-of-apps.yaml"
    "../manifests/argocd/applications/sln-staging.yaml"
    "../manifests/argocd/applications/sln-production.yaml"
    "../manifests/apps/staging/values-staging.yaml"
    "../manifests/apps/production/values-prod.yaml"
    "../manifests/apps/staging/namespace.yaml"
    "../manifests/apps/production/namespace.yaml"
    "../manifests/helm/spacelaunchnow/Chart.yaml"
    "../.github/workflows/build-staging-argocd.yml"
    "../.github/workflows/build-production-argocd.yml"
)

for file in "${yaml_files[@]}"; do
    if [[ -f "$file" ]]; then
        if validate_yaml "$file"; then
            log_success "Valid YAML: $file"
        fi
    fi
done

# Validate Helm chart
log_section "Helm Chart Validation"

if [[ -d "../manifests/helm/spacelaunchnow" ]]; then
    if validate_helm_chart "../manifests/helm/spacelaunchnow"; then
        log_success "Helm chart is valid"
        
        # Test template rendering with both environments
        if helm template test-release ../manifests/helm/spacelaunchnow -f ../manifests/apps/staging/values-staging.yaml >/dev/null 2>&1; then
            log_success "Helm template renders with staging values"
        else
            log_error "Helm template fails with staging values"
        fi
        
        if helm template test-release ../manifests/helm/spacelaunchnow -f ../manifests/apps/production/values-prod.yaml >/dev/null 2>&1; then
            log_success "Helm template renders with production values"
        else
            log_error "Helm template fails with production values"
        fi
    fi
fi

# Validate ArgoCD applications
log_section "ArgoCD Applications Validation"

# Check that ArgoCD applications reference correct paths
for app_file in ../manifests/argocd/applications/*.yaml; do
    if [[ -f "$app_file" ]]; then
        app_name=$(basename "$app_file" .yaml)
        source_path=$(yq eval '.spec.source.path' "$app_file" 2>/dev/null)
        
        if [[ "$source_path" != "null" && "$source_path" != "" ]]; then
            # Convert relative path to absolute for checking
            full_path="../manifests/$source_path"
            if [[ "$source_path" == manifests/* ]]; then
                full_path="../$source_path"
            fi
            
            if [[ -d "$full_path" ]]; then
                log_success "ArgoCD app '$app_name' source path exists: $source_path"
            else
                log_error "ArgoCD app '$app_name' source path missing: $source_path"
            fi
        fi
    fi
done

# Validate Ansible integration
log_section "Ansible Integration Validation"

# Check if ArgoCD is properly integrated in Ansible playbook
if grep -q "argo/argo-cd" deploy-sln.yml; then
    log_success "ArgoCD Helm chart is configured in Ansible playbook"
else
    log_error "ArgoCD Helm chart not found in Ansible playbook"
fi

if grep -q "argocd/values.yaml" deploy-sln.yml; then
    log_success "ArgoCD values file is referenced in Ansible playbook"
else
    log_error "ArgoCD values file not referenced in Ansible playbook"
fi

# Check if app-of-apps is deployed in post_tasks
if grep -q "sln-app-of-apps" deploy-sln.yml; then
    log_success "App-of-Apps is configured in Ansible playbook"
else
    log_error "App-of-Apps not found in Ansible playbook"
fi

# Validate GitHub Actions workflows
log_section "GitHub Actions Workflows Validation"

# Check staging workflow
if [[ -f "../.github/workflows/build-staging-argocd.yml" ]]; then
    if grep -q "manifests/apps/staging/values-staging.yaml" "../.github/workflows/build-staging-argocd.yml"; then
        log_success "Staging workflow references correct values file"
    else
        log_error "Staging workflow doesn't reference correct values file"
    fi
fi

# Check production workflow
if [[ -f "../.github/workflows/build-production-argocd.yml" ]]; then
    if grep -q "manifests/apps/production/values-prod.yaml" "../.github/workflows/build-production-argocd.yml"; then
        log_success "Production workflow references correct values file"
    else
        log_error "Production workflow doesn't reference correct values file"
    fi
fi

# Validate scripts
log_section "Deployment Scripts Validation"

scripts=(
    "run-deploy.sh"
    "deploy-argocd.sh"
    "../manifests/deploy-manifests.sh"
    "../manifests/validate-manifests.sh"
)

for script in "${scripts[@]}"; do
    if [[ -f "$script" ]]; then
        if [[ -x "$script" ]]; then
            log_success "Script is executable: $script"
        else
            log_warning "Script is not executable: $script"
        fi
    fi
done

# Check if cluster is accessible for live validation
log_section "Live Cluster Validation"

if kubectl cluster-info >/dev/null 2>&1; then
    # Check if ArgoCD is installed
    if kubectl get namespace argocd >/dev/null 2>&1; then
        log_success "ArgoCD namespace exists"
        
        # Check ArgoCD components
        if kubectl get deployment argocd-server -n argocd >/dev/null 2>&1; then
            ready_replicas=$(kubectl get deployment argocd-server -n argocd -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
            if [[ "$ready_replicas" -gt 0 ]]; then
                log_success "ArgoCD server is running"
            else
                log_warning "ArgoCD server is not ready"
            fi
        else
            log_warning "ArgoCD server deployment not found"
        fi
        
        # Check for existing applications
        if kubectl get applications -n argocd >/dev/null 2>&1; then
            app_count=$(kubectl get applications -n argocd --no-headers 2>/dev/null | wc -l)
            if [[ "$app_count" -gt 0 ]]; then
                log_info "Found $app_count ArgoCD applications"
                kubectl get applications -n argocd -o custom-columns="NAME:.metadata.name,SYNC:.status.sync.status,HEALTH:.status.health.status" 2>/dev/null || true
            else
                log_info "No ArgoCD applications found (this is expected before first deployment)"
            fi
        fi
    else
        log_info "ArgoCD not installed (this is OK - will be installed by Ansible)"
    fi
    
    # Check for SLN namespaces
    for ns in sln-dev sln-prod; do
        if kubectl get namespace "$ns" >/dev/null 2>&1; then
            log_info "Namespace '$ns' already exists"
        else
            log_info "Namespace '$ns' will be created by ArgoCD"
        fi
    done
else
    log_info "Skipping live cluster validation (cluster not accessible)"
fi

# Summary
log_section "Validation Summary"

echo
if [[ $ISSUES -eq 0 ]]; then
    log_success "🎉 GitOps migration validation PASSED!"
    echo
    echo -e "${GREEN}✅ Ready for deployment!${NC}"
    echo
    echo "Next steps:"
    echo "1. Deploy infrastructure: ./run-deploy.sh"
    echo "2. Deploy GitOps manifests: cd ../manifests && ./deploy-manifests.sh"
    echo "3. Monitor in ArgoCD UI: https://argo.spacelaunchnow.app"
else
    log_error "❌ GitOps migration validation FAILED!"
    echo
    echo -e "${RED}Found $ISSUES critical issue(s) that must be fixed before deployment.${NC}"
fi

if [[ $WARNINGS -gt 0 ]]; then
    echo -e "${YELLOW}Found $WARNINGS warning(s) that should be reviewed.${NC}"
fi

echo
echo -e "${BLUE}📖 For more details, see: GITOPS_MIGRATION.md${NC}"

exit $ISSUES
