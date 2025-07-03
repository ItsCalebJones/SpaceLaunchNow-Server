# Grafana Security Setup

## Overview
The Grafana admin password has been moved from hardcoded values to secure secret management.

## Security Changes Made

### 1. Removed Hardcoded Password
- ❌ **Before**: `adminPassword: <>`
- ✅ **After**: References secure Kubernetes secret

### 2. Configuration Update
The Grafana configuration in `k8s/monitoring/values_sln.yaml` now uses:
```yaml
grafana:
  admin:
    existingSecret: "grafana-admin-credentials"
    userKey: admin-user
    passwordKey: admin-password
```

## Setup Options

### Option 1: Using Vault + External Secrets (Recommended)

1. **Store credentials in Vault**:
   ```bash
   # Set a secure password
   GRAFANA_PASSWORD=$(openssl rand -base64 32)
   
   # Store in Vault
   vault kv put secret/grafana \
     admin-user="admin" \
     admin-password="$GRAFANA_PASSWORD"
   ```

2. **Apply External Secret**:
   ```bash
   kubectl apply -f k8s/secrets-management/grafana-external-secret.yaml
   ```

### Option 2: Manual Kubernetes Secret

1. **Generate secure password**:
   ```bash
   GRAFANA_PASSWORD=$(openssl rand -base64 32)
   echo "Generated password: $GRAFANA_PASSWORD"
   ```

2. **Create the secret manually**:
   ```bash
   kubectl create secret generic grafana-admin-credentials \
     --from-literal=admin-user=admin \
     --from-literal=admin-password="$GRAFANA_PASSWORD" \
     --namespace=metrics
   ```

### Option 3: Using Secret Template

1. **Copy the template**:
   ```bash
   cp k8s/secrets-management/grafana-admin-secret.yaml.template \
      k8s/secrets-management/grafana-admin-secret.yaml
   ```

2. **Edit the file** and replace `REPLACE_WITH_SECURE_PASSWORD`

3. **Apply the secret**:
   ```bash
   kubectl apply -f k8s/secrets-management/grafana-admin-secret.yaml
   ```

## Security Best Practices

### ✅ Do:
- Use strong, randomly generated passwords
- Store passwords in Vault or secure secret management
- Use External Secrets for automated secret rotation
- Never commit actual passwords to Git

### ❌ Don't:
- Hardcode passwords in YAML files
- Use simple or default passwords
- Commit secrets to version control
- Share passwords in plain text

## Accessing Grafana

1. **Get the admin password**:
   ```bash
   kubectl get secret grafana-admin-credentials -n metrics \
     -o jsonpath='{.data.admin-password}' | base64 -d
   ```

2. **Access Grafana**:
   - URL: https://grafana.spacelaunchnow.app
   - Username: admin
   - Password: (from secret above)

## Troubleshooting

### Secret Not Found Error
If Grafana pods fail to start with secret errors:

1. **Check if secret exists**:
   ```bash
   kubectl get secret grafana-admin-credentials -n metrics
   ```

2. **Verify External Secret status** (if using):
   ```bash
   kubectl get externalsecret grafana-admin-credentials -n metrics -o yaml
   ```

3. **Check Vault connectivity** (if using):
   ```bash
   kubectl logs -n external-secrets-system deployment/external-secrets -f
   ```

### Password Reset
To reset the Grafana admin password:

1. **Update the secret**:
   ```bash
   NEW_PASSWORD=$(openssl rand -base64 32)
   kubectl patch secret grafana-admin-credentials -n metrics \
     --type='json' \
     -p='[{"op": "replace", "path": "/data/admin-password", "value": "'$(echo -n "$NEW_PASSWORD" | base64)'"}]'
   ```

2. **Restart Grafana pod**:
   ```bash
   kubectl rollout restart deployment grafana-stack-grafana -n metrics
   ```

## Related Files
- `k8s/monitoring/values_sln.yaml` - Grafana Helm values
- `k8s/secrets-management/grafana-external-secret.yaml` - External Secret config
- `k8s/secrets-management/grafana-admin-secret.yaml.template` - Manual secret template
- `k8s/secrets-management/secrets-config.yaml` - Vault secret definition
