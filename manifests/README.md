# SpaceLaunchNow GitOps Manifests

This directory contains all Kubernetes manifests and ArgoCD configurations for SpaceLaunchNow deployment using GitOps principles.

## 🏗️ Structure

```
manifests/
├── README.md                    # This file
├── apps/                        # Environment-specific configurations
│   ├── staging/
│   │   ├── kustomization.yaml   # Kustomize configuration for staging
│   │   ├── values-staging.yaml  # Helm values for staging
│   │   └── namespace.yaml       # Staging namespace definition
│   └── production/
│       ├── kustomization.yaml   # Kustomize configuration for production
│       ├── values-prod.yaml     # Helm values for production
│       └── namespace.yaml       # Production namespace definition
├── argocd/                      # ArgoCD configurations
│   ├── applications/            # Application definitions
│   │   ├── sln-staging.yaml     # Staging application
│   │   ├── sln-production.yaml  # Production application
│   │   ├── sln-infrastructure.yaml # Infrastructure components
│   │   ├── sln-memcached-staging.yaml # Staging Memcached
│   │   └── sln-memcached-production.yaml # Production Memcached
│   ├── app-of-apps.yaml        # Meta-application
│   └── projects/               # ArgoCD projects
│       └── spacelaunchnow.yaml  # SpaceLaunchNow project definition
├── infrastructure/             # Infrastructure components
│   ├── kustomization.yaml      # Infrastructure kustomization
│   ├── external-secrets/       # External Secrets Operator configs
│   │   ├── kustomization.yaml
│   │   ├── sln-external-secrets-dev.yaml
│   │   └── sln-external-secrets-prod.yaml
│   └── memcached/              # Memcached configurations (reference values)
│       ├── values-staging.yaml
│       └── values-production.yaml
└── helm/                      # Helm charts
    └── spacelaunchnow/        # SpaceLaunchNow Helm chart
        ├── Chart.yaml
        ├── values.yaml        # Default values
        └── templates/         # Kubernetes templates
```

## 🎯 GitOps Workflow

### Development Flow
1. **Code Changes** → Push to `main` branch
2. **CI/CD Pipeline** → Builds Docker image and updates manifests
3. **ArgoCD Detection** → Automatically syncs staging environment
4. **Validation** → Staging deployment tested automatically

### Production Flow
1. **Manual Trigger** → Production deployment workflow
2. **Image Promotion** → Staging image promoted to production
3. **Manifest Update** → Production values updated
4. **Manual Review** → ArgoCD UI review required
5. **Manual Sync** → Production deployment approved and executed

## 🚀 Quick Start

### Prerequisites
- Kubernetes cluster with ArgoCD installed
- kubectl configured for cluster access
- Appropriate RBAC permissions

### Deploy Applications
```bash
# Apply ArgoCD project
kubectl apply -f argocd/projects/spacelaunchnow.yaml

# Deploy App-of-Apps (creates all applications)
kubectl apply -f argocd/app-of-apps.yaml

# Deploy infrastructure components (external secrets, etc.)
kubectl apply -f argocd/applications/sln-infrastructure.yaml

# Deploy Memcached for staging (automated)
kubectl apply -f argocd/applications/sln-memcached-staging.yaml

# Deploy Memcached for production (manual sync required)
kubectl apply -f argocd/applications/sln-memcached-production.yaml
```

### Monitor Deployments
- **ArgoCD UI**: https://argo.spacelaunchnow.app
- **Staging App**: https://argo.spacelaunchnow.app/applications/sln-staging
- **Production App**: https://argo.spacelaunchnow.app/applications/sln-production
- **Infrastructure**: https://argo.spacelaunchnow.app/applications/sln-infrastructure
- **Staging Memcached**: https://argo.spacelaunchnow.app/applications/sln-memcached-staging
- **Production Memcached**: https://argo.spacelaunchnow.app/applications/sln-memcached-production

## 🔧 Environment Configuration

### Staging Environment
- **Namespace**: `sln-dev`
- **Sync Policy**: Automated
- **Target**: Latest from `main` branch
- **Values**: `helm/spacelaunchnow/values-staging.yaml` (with overrides from `apps/staging/values-staging.yaml`)

### Production Environment
- **Namespace**: `sln-prod`
- **Sync Policy**: Manual approval required
- **Target**: Promoted images from staging
- **Values**: `helm/spacelaunchnow/values-prod.yaml` (with overrides from `apps/production/values-prod.yaml`)

### Infrastructure Components
- **External Secrets**: Automated sync for both environments
- **Memcached Staging**: Automated sync to `sln-dev` namespace
- **Memcached Production**: Manual sync to `sln-prod` namespace

## 📊 Monitoring

### Application Health
- ArgoCD monitors Kubernetes resource health
- Automatic drift detection and reconciliation
- Deployment history and rollback capabilities

### Key Metrics
- Sync status and frequency
- Application health status
- Resource utilization
- Deployment success rates

## 🔐 Security

### Secret Management
- Secrets managed via External Secrets Operator
- Integration with HashiCorp Vault
- No secrets stored in Git repository

### Access Control
- ArgoCD RBAC for team access
- Environment-specific permissions
- Audit trail for all changes

## 🛠️ Development

### Adding New Resources
1. Add Kubernetes manifests to appropriate environment directory
2. Update Kustomization files if using Kustomize
3. Commit changes to trigger ArgoCD sync

### Environment Promotion
1. Test changes in staging environment
2. Use production workflow to promote to production
3. Manual approval required for production deployment

## � Migration from Manual Helm

If you previously deployed Memcached manually using Helm commands, you should remove those deployments before applying the ArgoCD manifests:

```bash
# Remove existing manual Memcached deployments (if any)
helm uninstall llapi -n sln-dev 2>/dev/null || true
helm uninstall llapi-dev -n sln-dev 2>/dev/null || true  
helm uninstall sln-staging-memcached -n sln-dev 2>/dev/null || true
helm uninstall sln-prod-memcache -n sln-prod 2>/dev/null || true

# Then apply the ArgoCD applications
kubectl apply -f argocd/applications/sln-memcached-staging.yaml
kubectl apply -f argocd/applications/sln-memcached-production.yaml
```

## �📚 Documentation

- **Helm Chart**: [helm/spacelaunchnow/README.md](helm/spacelaunchnow/README.md)
- **ArgoCD Setup**: [../k8s/README.md](../k8s/README.md)
- **CI/CD Integration**: [../.github/CICD_README.md](../.github/CICD_README.md)

---

**🔗 Links**
- [ArgoCD UI](https://argo.spacelaunchnow.app)
- [SpaceLaunchNow](https://spacelaunchnow.me)
- [The Space Devs](https://thespacedevs.com)
