# Google OAuth Setup Guide for ArgoCD

## Prerequisites
- Google Cloud Console access
- kubectl access to your Kubernetes cluster
- Helm installed

## Step 1: Create Google OAuth2 Application

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create or select a project
3. Navigate to "APIs & Services" > "Credentials"
4. Click "Create Credentials" > "OAuth 2.0 Client IDs"
5. Configure the OAuth consent screen if not already done
6. Set application type to "Web application"
7. Add these authorized redirect URIs:
   ```
   https://argo.spacelaunchnow.app/auth/callback
   ```
8. Save and note down the Client ID and Client Secret

## Step 2: Create Kubernetes Secret

1. Copy the template file:
   ```bash
   cp google-oauth-secret.yaml.template google-oauth-secret.yaml
   ```

2. Edit `google-oauth-secret.yaml` and replace the placeholders:
   ```yaml
   stringData:
     oidc.google.clientId: "your-actual-client-id.apps.googleusercontent.com"
     oidc.google.clientSecret: "your-actual-client-secret"
   ```

3. Apply the secret:
   ```bash
   kubectl apply -f google-oauth-secret.yaml
   ```

4. **Important**: Add `google-oauth-secret.yaml` to `.gitignore` to avoid committing secrets!

## Step 3: Update RBAC Configuration

Edit the values.yaml file and update the RBAC section with your Google email addresses:

```yaml
rbac:
  policy.csv: |
    # Add your Google email to assign admin role
    g, your-email@gmail.com, role:admin
    g, developer@yourdomain.com, role:developer
```

## Step 4: Deploy ArgoCD with OAuth

1. Upgrade the Helm release:
   ```bash
   helm upgrade argocd argo/argo-cd -n argocd -f values.yaml
   ```

2. Wait for pods to restart:
   ```bash
   kubectl get pods -n argocd -w
   ```

## Step 5: Test Login

1. Go to https://argo.spacelaunchnow.app
2. Click "Log In Via Google" button
3. Authenticate with your Google account
4. You should be logged in with the appropriate role

## Troubleshooting

### Common Issues:

1. **Redirect URI mismatch**: Make sure the redirect URI in Google Console exactly matches `https://argo.spacelaunchnow.app/auth/callback`

2. **Secret not found**: Verify the secret exists:
   ```bash
   kubectl get secret argocd-secret -n argocd -o yaml
   ```

3. **User not authorized**: Check RBAC configuration and ensure your Google email is mapped to a role

4. **OAuth consent screen**: Make sure your OAuth consent screen is configured and published

### Useful Commands:

- Check ArgoCD server logs:
  ```bash
  kubectl logs -n argocd -l app.kubernetes.io/component=server
  ```

- Check current configuration:
  ```bash
  kubectl get configmap argocd-cmd-params-cm -n argocd -o yaml
  ```

- Restart ArgoCD server:
  ```bash
  kubectl rollout restart deployment argocd-server -n argocd
  ```

## Security Notes

1. Never commit OAuth secrets to git
2. Use least privilege principle for RBAC roles
3. Consider using Google Workspace groups for easier user management
4. Regularly rotate OAuth client secrets
5. Monitor login attempts and access patterns

## Next Steps

- Configure Google Workspace groups if using Google Workspace
- Set up proper monitoring and alerting
- Consider adding additional OIDC providers if needed
- Implement proper backup and disaster recovery procedures
