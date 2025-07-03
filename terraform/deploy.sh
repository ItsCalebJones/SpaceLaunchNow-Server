#!/bin/bash
set -e

echo "🚀 SLN Infrastructure Deployment Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "main.tf" ]; then
    print_error "Please run this script from the terraform directory"
    exit 1
fi

# Check if terraform.tfvars exists
if [ ! -f "terraform.tfvars" ]; then
    print_warning "terraform.tfvars not found. Please create it from terraform.tfvars.example"
    echo "Required variables:"
    echo "- do_token"
    echo "- cloudflare_api_token"
    exit 1
fi

print_status "Step 1: Creating Kubernetes cluster and infrastructure..."

# Initialize and apply main infrastructure
terraform init
terraform plan -target=digitalocean_kubernetes_cluster.sln_k8s_prod -target=digitalocean_vpc.sln_vpc -target=digitalocean_container_registry.sln_registry
read -p "Proceed with cluster creation? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -target=digitalocean_kubernetes_cluster.sln_k8s_prod -target=digitalocean_vpc.sln_vpc -target=digitalocean_container_registry.sln_registry -auto-approve
else
    print_warning "Cluster creation cancelled"
    exit 1
fi

print_status "Step 2: Saving kubeconfig..."
terraform apply -target=local_file.kubeconfig -auto-approve

# Set KUBECONFIG
export KUBECONFIG=$(pwd)/sln-prod-kubeconfig-01
print_status "KUBECONFIG set to: $KUBECONFIG"

print_status "Step 3: Running Ansible deployment..."

# Extract Cloudflare API token from terraform.tfvars
CLOUDFLARE_TOKEN=$(grep '^cloudflare_api_token' terraform.tfvars | sed 's/.*= *"\([^"]*\)".*/\1/')
if [ -z "$CLOUDFLARE_TOKEN" ]; then
    print_error "Could not extract cloudflare_api_token from terraform.tfvars"
    exit 1
fi

cd ../k8s
if [ -f "run-deploy.sh" ]; then
    chmod +x run-deploy.sh
    ./run-deploy.sh --cloudflare-token "$CLOUDFLARE_TOKEN"
else
    print_error "Ansible deployment script not found"
    exit 1
fi

print_status "Step 4: Waiting for load balancer to be ready..."
# Wait for the LoadBalancer service to get an external IP
print_status "Waiting for LoadBalancer external IP to be assigned..."
timeout=300
elapsed=0
while [ $elapsed -lt $timeout ]; do
    LB_IP=$(kubectl get service nginx-ingress-ingress-nginx-controller -n nginx-ingress -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "")
    if [ -n "$LB_IP" ] && [ "$LB_IP" != "null" ]; then
        print_status "LoadBalancer IP assigned: $LB_IP"
        break
    fi
    echo "Waiting for LoadBalancer IP... ($elapsed/$timeout seconds)"
    sleep 10
    elapsed=$((elapsed + 10))
done

if [ $elapsed -ge $timeout ]; then
    print_error "Timeout waiting for LoadBalancer IP assignment"
    exit 1
fi

print_status "Step 5: Creating DNS record..."
cd ../terraform

# Apply DNS configuration
terraform plan -target=cloudflare_record.spacelaunchnow_app -target=cloudflare_record.wildcard_spacelaunchnow_app
read -p "Create DNS records? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -target=cloudflare_record.spacelaunchnow_app -target=cloudflare_record.wildcard_spacelaunchnow_app -auto-approve
else
    print_warning "DNS record creation skipped"
fi

print_status "Deployment completed! 🎉"
echo ""
echo "Resources created:"
echo "- Kubernetes cluster: sln-prod-k8s-01"
echo "- Container registry: sln-prod-registry-01"
echo "- VPC: sln-prod-vpc-01"
echo "- DNS record: spacelaunchnow.app"
echo "- Wildcard DNS record: *.spacelaunchnow.app"
echo ""
echo "Next steps:"
echo "1. Configure your applications to use the new cluster"
echo "2. Push container images to: registry.digitalocean.com/sln-prod-registry-01"
echo "3. Access your services at: https://spacelaunchnow.app"
echo "4. All subdomains under *.spacelaunchnow.app will resolve to the cluster"
