# SpaceLaunchNow ArgoCD Setup

Complete ArgoCD deployment and CI/CD integration for SpaceLaunchNow.

## 🚀 Quick Start

### All-in-One Setup (Recommended)
```bash
# Deploy ArgoCD + Setup CI/CD integration
./setup-cicd.sh

# Just deploy ArgoCD (no CI/CD setup)
./setup-cicd.sh --deploy-only

# Just setup CI/CD integration (ArgoCD already deployed)
./setup-cicd.sh --cicd-only
```

### Legacy Deployment
```bash
# Deploy ArgoCD only (legacy method)
./deploy.sh
```

## 📁 Directory Structure

```
k8s/argocd/
├── README.md                           # This file
├── setup-cicd.sh                       # All-in-one deployment + CI/CD setup
├── deploy.sh                           # Legacy ArgoCD deployment only
├── values.yaml                         # ArgoCD Helm values
├── CICD_INTEGRATION.md                 # CI/CD integration guide
├── google-oauth-secret.yaml.template   # OAuth secret template
└── GOOGLE_OAUTH_SETUP.md               # OAuth setup guide
```

## 🤖 CI/CD Integration

The `setup-cicd.sh` script provides complete automation:

1. **🏗️ Deploys ArgoCD** using Helm with production-ready configuration
2. **🔐 Generates CI/CD token** for GitHub Actions integration
3. **🧪 Tests connectivity** and permissions
4. **📖 Provides setup instructions** for GitHub secrets

### GitHub Actions Integration

After running the setup script, you'll get a token to add to GitHub:

1. **Go to your repository:** Settings → Secrets and variables → Actions
2. **Add new secret:** `ARGOCD_TOKEN`
3. **Use the token** provided by the setup script

### ArgoCD CLI Quick Reference

```bash
# Login to ArgoCD
argocd login argo.spacelaunchnow.app

# List applications
argocd app list

# Sync application
argocd app sync sln-production

# Rollback application
argocd app rollback sln-production

# View application history
argocd app history sln-production
```

## 🔧 Configuration

All ArgoCD configuration is in `values.yaml`:
- **Ingress**: Configured with TLS and Let's Encrypt
- **RBAC**: Google OAuth integration with role-based access
- **Resources**: Optimized resource limits
- **Monitoring**: Prometheus metrics enabled

## 🔑 Access

After deployment:
- **URL**: https://argo.spacelaunchnow.app
- **Username**: admin
- **Password**: Retrieved from Kubernetes secret (shown in deployment output)

## Prerequisites

- **kubectl**: Configured for target cluster
- **helm**: Installed and working
- **Cluster admin permissions**
- **cert-manager**: Installed for TLS certificates
- **DNS**: `argo.spacelaunchnow.app` pointing to your ingress

## 🛠️ Management Commands

### ArgoCD CLI Setup
```bash
# Install ArgoCD CLI
curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd

# Login to ArgoCD
argocd login argo.spacelaunchnow.app
```

### Application Management
```bash
# List applications
argocd app list

# Sync application
argocd app sync sln-staging

# Wait for healthy status
argocd app wait sln-staging --health --timeout 300

# Rollback to previous version
argocd app rollback sln-production

# Get application status
kubectl get applications -n argocd

# Check ArgoCD pods
kubectl get pods -n argocd
```

### CI/CD Integration
```bash
# Generate token for GitHub Actions
argocd account generate-token --account admin --expires-in 8760h

# Test CI/CD access
echo "TOKEN" | argocd login argo.spacelaunchnow.app --username admin --password-stdin --insecure
```

**📖 See [CI/CD Integration Guide](CICD_INTEGRATION.md) for complete setup.**

## 🔧 Troubleshooting

```bash
# Check ArgoCD server logs
kubectl logs deployment/argocd-server -n argocd

# Port forward for local access
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Validate deployment
./validate-deployment.sh
```

## 📚 Additional Documentation

- **[CI/CD Integration](CICD_INTEGRATION.md)**: GitHub Actions integration setup
- **[Google OAuth Setup](GOOGLE_OAUTH_SETUP.md)**: SSO configuration guide
- **[Migration Checklist](migration-checklist.md)**: Step-by-step migration guide (if exists)
- **[Helm Integration](helm-integration.md)**: Detailed Helm chart integration (if exists)
- **[Application Configuration](applications.md)**: ArgoCD application reference (if exists)

---

**🔗 ArgoCD UI**: https://argo.spacelaunchnow.app  
**📅 Last Updated**: June 28, 2025  
**👥 Maintained By**: SpaceLaunchNow DevOps Team
