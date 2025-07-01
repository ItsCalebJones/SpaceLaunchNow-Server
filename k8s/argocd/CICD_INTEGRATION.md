# 🤖 ArgoCD CI/CD Integration Setup

This guide configures ArgoCD for integration with GitHub Actions CI/CD workflows.

## Overview

The CI/CD integration allows GitHub Actions to:
- ✅ Trigger ArgoCD application syncs
- 🔍 Monitor deployment status and health
- ⏪ Execute rollbacks via ArgoCD CLI
- 📊 Verify application health after deployments

## 🔑 Admin Token Setup for CI/CD

### Step 1: Generate Admin Token

```bash
# Login to ArgoCD
argocd login argo.spacelaunchnow.app

# Generate a long-lived token for CI/CD
argocd account generate-token --account admin --expires-in 8760h
```

**Alternative via UI:**
1. Go to https://argo.spacelaunchnow.app
2. Settings → Accounts → admin
3. Generate New Token
4. Set expiration (1 year recommended)
5. Copy the generated token

### Step 2: Add Token to GitHub Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Name: `ARGOCD_TOKEN`
5. Value: Paste the token from Step 1
6. Save

### Step 3: Verify Token Access

Test the token works with ArgoCD CLI:

```bash
# Test login with token
echo "YOUR_TOKEN_HERE" | argocd login argo.spacelaunchnow.app --username admin --password-stdin --insecure

# Verify access to applications
argocd app list

# Test sync operation
argocd app sync sln-staging --dry-run
```

## 🔧 Service Account Setup (Alternative Approach)

For more granular permissions, you can create a dedicated service account:

### Step 1: Create Service Account

```bash
# Create namespace if it doesn't exist
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -

# Create service account
kubectl create serviceaccount github-actions -n argocd
```

### Step 2: Create RBAC Configuration

```yaml
# Save as github-actions-rbac.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: argocd
  name: github-actions-role
rules:
- apiGroups: ["argoproj.io"]
  resources: ["applications"]
  verbs: ["get", "list", "patch", "sync"]
- apiGroups: [""]
  resources: ["events"]
  verbs: ["list"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: github-actions-binding
  namespace: argocd
subjects:
- kind: ServiceAccount
  name: github-actions
  namespace: argocd
roleRef:
  kind: Role
  name: github-actions-role
  apiGroup: rbac.authorization.k8s.io
---
# ArgoCD RBAC policy for service account
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
  labels:
    app.kubernetes.io/name: argocd-rbac-cm
    app.kubernetes.io/part-of: argocd
data:
  policy.csv: |
    p, github-actions, applications, *, */*, allow
    p, github-actions, repositories, *, *, allow
    p, github-actions, logs, get, *, allow
  scopes: '[groups]'
```

```bash
# Apply RBAC configuration
kubectl apply -f github-actions-rbac.yaml
```

### Step 3: Generate Service Account Token

```bash
# Create token for service account (1 year expiration)
kubectl create token github-actions -n argocd --duration=8760h
```

### Step 4: Configure ArgoCD for Service Account

```bash
# Update ArgoCD to recognize the service account
kubectl patch configmap argocd-cm -n argocd --patch '
data:
  accounts.github-actions: "apiKey"
  accounts.github-actions.enabled: "true"
'

# Restart ArgoCD server to pick up changes
kubectl rollout restart deployment/argocd-server -n argocd
```

## 🚀 GitHub Actions Integration

### Workflow Configuration

Your GitHub Actions workflows will use these ArgoCD CLI commands:

```yaml
# Example workflow step
- name: 🔧 Install ArgoCD CLI
  run: |
    curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
    sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
    rm argocd-linux-amd64

- name: 🔐 Login to ArgoCD
  run: |
    echo "${{ secrets.ARGOCD_TOKEN }}" | argocd login argo.spacelaunchnow.app --username admin --password-stdin --insecure

- name: 🔄 Sync Application
  run: |
    argocd app sync sln-production --timeout 300

- name: ✅ Wait for Health
  run: |
    argocd app wait sln-production --health --timeout 300
```

### Common ArgoCD CLI Commands for CI/CD

```bash
# Application Management
argocd app list                           # List all applications
argocd app get sln-production            # Get application details
argocd app sync sln-production           # Sync application
argocd app wait sln-production --health  # Wait for healthy status

# Rollback Operations
argocd app history sln-production        # View deployment history
argocd app rollback sln-production       # Rollback to previous version
argocd app rollback sln-production --revision 123  # Rollback to specific revision

# Status and Monitoring
argocd app get sln-production -o json | jq '.status.health.status'  # Get health status
argocd app get sln-production -o json | jq '.status.summary.images[]'  # Get current images
```

## 🔍 Monitoring and Troubleshooting

### Health Checks

```bash
# Check ArgoCD server health
kubectl get pods -n argocd -l app.kubernetes.io/name=argocd-server

# Check application sync status
argocd app get sln-production --output json | jq '.status.sync'

# View recent events
kubectl get events -n argocd --sort-by=.metadata.creationTimestamp
```

### Common Issues

**Token Authentication Failed:**
```bash
# Verify token hasn't expired
argocd account get-user-info

# Check ArgoCD server logs
kubectl logs deployment/argocd-server -n argocd --tail=50
```

**Application Sync Issues:**
```bash
# Check application status
argocd app get sln-production --show-operation

# View sync operation details
kubectl describe application sln-production -n argocd
```

**Permission Denied:**
```bash
# Verify RBAC configuration
kubectl auth can-i sync applications --as=system:serviceaccount:argocd:github-actions -n argocd

# Check ArgoCD RBAC policy
kubectl get configmap argocd-rbac-cm -n argocd -o yaml
```

## 🔒 Security Best Practices

### Token Management
- ✅ **Rotate tokens annually** - Set calendar reminders
- ✅ **Use minimal permissions** - Prefer service accounts over admin tokens
- ✅ **Monitor token usage** - Check ArgoCD audit logs regularly
- ✅ **Secure storage** - Only store in GitHub Secrets, never in code

### Access Control
- ✅ **Separate environments** - Different tokens for staging/production if needed
- ✅ **Audit access** - Review who has ArgoCD access quarterly
- ✅ **Monitor operations** - Set up alerts for rollbacks and failed syncs
- ✅ **Document procedures** - Keep this guide updated

### Network Security
- ✅ **TLS encryption** - Always use HTTPS/TLS for ArgoCD
- ✅ **Network policies** - Restrict ArgoCD access as needed
- ✅ **VPN/firewall** - Consider additional network restrictions

## 📋 Deployment Checklist

### Initial Setup
- [ ] ArgoCD deployed and accessible
- [ ] Admin password retrieved and secured
- [ ] DNS configured for argo.spacelaunchnow.app
- [ ] TLS certificates working

### CI/CD Integration
- [ ] Admin token generated and tested
- [ ] GitHub secret `ARGOCD_TOKEN` configured
- [ ] GitHub Actions workflows updated
- [ ] Test deployment executed successfully

### Security Validation
- [ ] Token permissions verified (minimal access)
- [ ] RBAC configuration reviewed
- [ ] Audit logging enabled
- [ ] Token rotation scheduled

### Monitoring Setup
- [ ] ArgoCD metrics enabled
- [ ] Alerts configured for sync failures
- [ ] Dashboard created for deployment tracking
- [ ] Team trained on rollback procedures

## 📚 Related Documentation

- **[GitHub Actions Workflows](../.github/workflows/)** - CI/CD pipeline configuration
- **[Rollback Guide](../.github/ROLLBACK_GUIDE.md)** - Emergency procedures
- **[CICD README](../.github/CICD_README.md)** - Complete CI/CD documentation

---

**⚡ Quick Test:** `argocd app list` should return your applications  
**🔗 ArgoCD UI:** https://argo.spacelaunchnow.app  
**📅 Last Updated:** June 30, 2025
