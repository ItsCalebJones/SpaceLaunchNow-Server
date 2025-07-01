#!/bin/bash

# Deploy ArgoCD for SpaceLaunchNow
# This script deploys only the ArgoCD components using Ansible

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Deploying ArgoCD for SpaceLaunchNow"
echo "=================================="

# Check if cloudflare token is provided
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "⚠️  CLOUDFLARE_API_TOKEN environment variable not set"
    echo "This is needed for certificate management"
    echo ""
    echo "Usage: CLOUDFLARE_API_TOKEN=your_token ./deploy-argocd.sh"
    echo "Or run the full deployment: ./run-deploy.sh"
    exit 1
fi

echo "ℹ️  Running ArgoCD deployment with Ansible..."

# Run only ArgoCD-related tags
ansible-playbook \
    "$SCRIPT_DIR/deploy-sln.yml" \
    -e cloudflare_api_token="$CLOUDFLARE_API_TOKEN" \
    --tags "helm_repos,cert_manager,argocd" \
    -v

echo ""
echo "✅ ArgoCD deployment completed!"
echo ""
echo "🔑 Getting ArgoCD admin password..."

# Wait a moment for the secret to be created
sleep 10

if kubectl get secret argocd-initial-admin-secret -n argocd &>/dev/null; then
    ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d)
    echo ""
    echo "🎉 ArgoCD is ready!"
    echo "==================="
    echo "URL: https://argo.spacelaunchnow.app"
    echo "Username: admin"
    echo "Password: $ADMIN_PASSWORD"
    echo ""
    echo "⚠️  IMPORTANT: Save this password - the secret will be deleted after first login!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Login to ArgoCD UI and change admin password"
    echo "2. Deploy GitOps applications:"
    echo "   cd ../manifests && ./deploy-manifests.sh"
    echo "3. Test staging deployment by pushing to main branch"
else
    echo "⚠️  ArgoCD admin secret not found. The deployment may still be starting."
    echo "Check the password later with:"
    echo "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
fi

echo ""
echo "🔗 Useful commands:"
echo "# Check ArgoCD status"
echo "kubectl get pods -n argocd"
echo ""
echo "# Access ArgoCD via port-forward (if ingress not working)"
echo "kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "# Install ArgoCD CLI"
echo "curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64"
echo "sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd"
