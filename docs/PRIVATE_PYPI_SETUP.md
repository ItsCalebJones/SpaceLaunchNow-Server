# Private PyPI Repository Setup

## Overview
SpaceLaunchNow uses a private PyPI repository hosted at `pypi.thespacedevs.com` for the custom package `django-launch-library`.

## Repository Configuration

### pyproject.toml Configuration
```toml
[[tool.poetry.source]]
name = "tsd"
url = "https://pypi.thespacedevs.com/simple/"
priority = "supplemental"
```

### Environment Variables Required
- `POETRY_HTTP_BASIC_TSD_USERNAME`: Username for private PyPI access
- `POETRY_HTTP_BASIC_TSD_PASSWORD`: Password/token for private PyPI access

## CI/CD Setup

### GitHub Secrets Required
Set these secrets in your GitHub repository:
- `PRIVATE_USERNAME`: Username for pypi.thespacedevs.com
- `PRIVATE_PASSWORD`: Password/token for pypi.thespacedevs.com

### Workflow Configuration
In GitHub Actions workflows, configure Poetry before installing dependencies:

```yaml
- name: 📦 Install Dependencies
  run: |
    # Configure Poetry for private repository access
    poetry config http-basic.tsd ${{ secrets.PRIVATE_USERNAME }} ${{ secrets.PRIVATE_PASSWORD }}
    poetry install --all-extras --with dev
```

## Local Development Setup

### Option 1: Environment Variables
```bash
export POETRY_HTTP_BASIC_TSD_USERNAME="your-username"
export POETRY_HTTP_BASIC_TSD_PASSWORD="your-password"
poetry install
```

### Option 2: Poetry Config
```bash
poetry config http-basic.tsd your-username your-password
poetry install
```

### Option 3: Keyring (Recommended for Security)
```bash
# Install keyring support
pip install keyring

# Store credentials securely
poetry config http-basic.tsd your-username
# Poetry will prompt for password and store it in system keyring
poetry install
```

## Troubleshooting

### Authorization Error
If you see: `Authorization error accessing https://pypi.thespacedevs.com/simple/`

1. **Check credentials**: Verify USERNAME and PASSWORD are correct
2. **Check network**: Ensure you can access pypi.thespacedevs.com
3. **Clear cache**: `poetry cache clear tsd --all`
4. **Reconfigure**: `poetry config --unset http-basic.tsd` then reconfigure

### Package Not Found
If you see: `Could not find a version that satisfies the requirement django-launch-library`

1. **Check package exists**: Verify the package is published to the private repo
2. **Check version**: Ensure the version specified in pyproject.toml exists
3. **Check source priority**: Ensure `priority = "supplemental"` is set correctly

### Cache Issues
```bash
# Clear all Poetry caches
poetry cache clear --all

# Clear specific repository cache
poetry cache clear tsd --all

# Force reinstall dependencies
poetry install --no-cache
```
