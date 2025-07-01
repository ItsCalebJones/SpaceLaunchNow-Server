#!/bin/bash

# Vault Secrets Manager
# Reads secrets-config.yaml and creates/updates secrets in Vault

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Check if yq is installed
if ! command -v yq >/dev/null 2>&1; then
    log_error "yq is required but not installed. Please install yq:"
    echo "  # Ubuntu/Debian:"
    echo "  sudo snap install yq"
    echo "  # Or download from: https://github.com/mikefarah/yq/releases"
    exit 1
fi

# Check if we're in the right directory and file is accessible
if [[ ! -f "secrets-config.yaml" ]]; then
    log_error "secrets-config.yaml not found. Please run this script from the secrets-management directory."
    exit 1
fi

if [[ ! -r "secrets-config.yaml" ]]; then
    log_error "Cannot read secrets-config.yaml. Please check file permissions:"
    echo "  chmod 644 secrets-config.yaml"
    exit 1
fi

# Check if Vault is accessible (only for sync command)
check_vault_access() {
    if ! vault status >/dev/null 2>&1; then
        log_error "Cannot connect to Vault. Please ensure:"
        echo "  1. Vault is running"
        echo "  2. VAULT_ADDR is set (e.g., export VAULT_ADDR=http://localhost:8200)"
        echo "  3. VAULT_TOKEN is set with appropriate permissions"
        exit 1
    fi
}

# Function to populate a single secret
populate_secret() {
    local secret_name="$1"
    local secret_path="$2"
    local description="$3"
    
    log_info "Processing secret: $secret_name"
    
    # Check if secret already exists
    if vault kv get "$secret_path" >/dev/null 2>&1; then
        log_warning "$secret_name already exists, skipping..."
        return 0
    fi
    
    # Build vault command arguments
    local vault_args=()
    
    # Read all key-value pairs for this secret
    while IFS= read -r key; do
        if [[ -n "$key" ]]; then
            value=$(cat secrets-config.yaml | yq eval ".secrets.${secret_name}.data.${key}" -)
            vault_args+=("${key}=${value}")
        fi
    done < <(cat secrets-config.yaml | yq eval ".secrets.${secret_name}.data | keys | .[]" -)
    
    # Create the secret
    if [[ ${#vault_args[@]} -gt 0 ]]; then
        vault kv put "$secret_path" "${vault_args[@]}" >/dev/null
        log_success "Created secret: $secret_name (${#vault_args[@]} keys)"
    else
        log_warning "No data found for secret: $secret_name"
    fi
}

# Function to list all configured secrets
list_secrets() {
    log_info "Configured secrets:"
    
    # Try yq first, fall back to grep if needed
    if cat secrets-config.yaml | yq eval '.secrets | keys | .[]' - >/dev/null 2>&1; then
        log_info "Using yq for detailed parsing..."
        secrets=$(cat secrets-config.yaml | yq eval '.secrets | keys | .[]' -)
        while read -r secret; do
            if [[ -n "$secret" ]]; then
                path=$(cat secrets-config.yaml | yq eval ".secrets.${secret}.path" - 2>/dev/null || echo "N/A")
                description=$(cat secrets-config.yaml | yq eval ".secrets.${secret}.description" - 2>/dev/null || echo "N/A")
                key_count=$(cat secrets-config.yaml | yq eval ".secrets.${secret}.data | length" - 2>/dev/null || echo "N/A")
                echo "  📦 $secret"
                echo "     Path: $path"
                echo "     Description: $description"
                echo "     Keys: $key_count"
                echo ""
            fi
        done <<< "$secrets"
    else
        log_warning "yq parsing failed, showing basic config structure:"
        echo ""
        echo "📋 Secrets defined in secrets-config.yaml:"
        # Fallback: use grep to extract secret names
        grep -E "^  [a-zA-Z0-9-]+:" secrets-config.yaml | sed 's/://g' | sed 's/^  /  📦 /'
        echo ""
        echo "💡 To see full details, fix yq permissions or run from a different location"
    fi
}

# Function to sync all secrets
sync_all_secrets() {
    log_info "🔄 Syncing all secrets from configuration..."
    
    # Try yq parsing first
    if cat secrets-config.yaml | yq eval '.secrets | keys | .[]' - >/dev/null 2>&1; then
        log_info "Using yq for YAML parsing..."
        secrets=$(cat secrets-config.yaml | yq eval '.secrets | keys | .[]' -)
        while read -r secret; do
            if [[ -n "$secret" ]]; then
                path=$(cat secrets-config.yaml | yq eval ".secrets.${secret}.path" -)
                description=$(cat secrets-config.yaml | yq eval ".secrets.${secret}.description" -)
                populate_secret "$secret" "$path" "$description"
            fi
        done <<< "$secrets"
    else
        log_warning "yq parsing failed, falling back to hardcoded secrets..."
        log_info "Creating the three main secrets manually..."
        
        # Fallback: Create the main secrets manually
        create_sln_dev_secret
        create_sln_prod_secret  
        create_cloudflare_secret
    fi
    
    log_success "✅ Secret synchronization complete!"
}

# Function to show usage
show_usage() {
    echo "Vault Secrets Manager"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  sync          Sync all secrets from secrets-config.yaml to Vault"
    echo "  list          List all configured secrets"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 sync       # Create/update all secrets in Vault"
    echo "  $0 list       # Show all configured secrets"
    echo ""
    echo "Prerequisites:"
    echo "  - Vault must be running and accessible"
    echo "  - VAULT_ADDR and VAULT_TOKEN environment variables must be set"
    echo "  - yq must be installed for YAML parsing"
}

# Fallback functions for when yq parsing fails
create_sln_dev_secret() {
    if vault kv get secret/sln-app-dev >/dev/null 2>&1; then
        log_warning "sln-app-dev already exists, skipping..."
        return 0
    fi
    
    log_info "Creating sln-app-dev secret..."
    vault kv put secret/sln-app-dev \
        django-secret-key="dev-django-secret-key-placeholder" \
        database-username="spacelaunchnow_dev" \
        database-password="dev-database-password-placeholder" \
        database-host="postgresql-dev.example.com" \
        database-port="5432" \
        aws-access-key-id="dev-aws-access-key-placeholder" \
        aws-secret-access-key="dev-aws-secret-key-placeholder" \
        do-cluster-id="dev-cluster-id-placeholder" \
        do-token="dev-do-token-placeholder" \
        email-host-user="noreply@spacelaunchnow.app" \
        email-host-password="dev-email-password-placeholder" \
        google-api-key="dev-google-api-key-placeholder" \
        google-analytics-tracking-id="GA-XXXXXXXX-X" \
        token-key="dev-token-key-placeholder" \
        token-secret="dev-token-secret-placeholder" \
        consumer-key="dev-consumer-key-placeholder" \
        consumer-secret="dev-consumer-secret-placeholder" \
        fcm-key="dev-fcm-key-placeholder" \
        fcm-project-id="spacelaunchnow-dev" \
        fcm-credentials="dev-fcm-credentials-json-placeholder" \
        discord-webhook="https://discord.com/api/webhooks/dev-webhook-placeholder" \
        discord-webhook-notification="https://discord.com/api/webhooks/dev-notification-placeholder" \
        sln-sentry-key="https://dev123placeholder@o123456.ingest.sentry.io/7891011" >/dev/null
    log_success "Created sln-app-dev secret (23 keys)"
}

create_sln_prod_secret() {
    if vault kv get secret/sln-app >/dev/null 2>&1; then
        log_warning "sln-app already exists, skipping..."
        return 0
    fi
    
    log_info "Creating sln-app secret..."
    vault kv put secret/sln-app \
        django-secret-key="prod-django-secret-key-placeholder" \
        database-username="spacelaunchnow_prod" \
        database-password="prod-database-password-placeholder" \
        database-host="postgresql-prod.example.com" \
        database-port="5432" \
        aws-access-key-id="prod-aws-access-key-placeholder" \
        aws-secret-access-key="prod-aws-secret-key-placeholder" \
        do-cluster-id="prod-cluster-id-placeholder" \
        do-token="prod-do-token-placeholder" \
        email-host-user="noreply@spacelaunchnow.app" \
        email-host-password="prod-email-password-placeholder" \
        google-api-key="prod-google-api-key-placeholder" \
        google-analytics-tracking-id="GA-XXXXXXXX-Y" \
        token-key="prod-token-key-placeholder" \
        token-secret="prod-token-secret-placeholder" \
        consumer-key="prod-consumer-key-placeholder" \
        consumer-secret="prod-consumer-secret-placeholder" \
        fcm-key="prod-fcm-key-placeholder" \
        fcm-project-id="spacelaunchnow-prod" \
        fcm-credentials="prod-fcm-credentials-json-placeholder" \
        discord-webhook="https://discord.com/api/webhooks/prod-webhook-placeholder" \
        discord-webhook-notification="https://discord.com/api/webhooks/prod-notification-placeholder" \
        sln-sentry-key="https://prod456placeholder@o123456.ingest.sentry.io/7891012" >/dev/null
    log_success "Created sln-app secret (23 keys)"
}

create_cloudflare_secret() {
    if vault kv get secret/cloudflare >/dev/null 2>&1; then
        log_warning "cloudflare already exists, skipping..."
        return 0
    fi
    
    log_info "Creating cloudflare secret..."
    vault kv put secret/cloudflare \
        api_token="cloudflare-api-token-placeholder" >/dev/null
    log_success "Created cloudflare secret (1 key)"
}

# Main logic
case "${1:-sync}" in
    "sync")
        check_vault_access
        sync_all_secrets
        ;;
    "list")
        list_secrets
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
