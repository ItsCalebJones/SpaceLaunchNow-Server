# SpaceLaunchNow Server - Copilot Instructions

## Architecture Overview

SpaceLaunchNow Server is a Django-based consumer application that extends the Launch Library API ecosystem with notifications, autoscaling, and web frontend capabilities. It integrates with:

- **LaunchLibrary-API**: Source of space launch data via shared models
- **SpaceLaunchNow-GitOps**: Kubernetes deployment and infrastructure management
- **External Services**: Firebase Cloud Messaging, DigitalOcean, Buffer API

## Core Components

### Application Structure
- `src/app/` - Core Django app with shared utilities
- `src/bot/` - Notification engine and social media posting
- `src/autoscaler/` - Kubernetes node pool scaling based on launch predictions
- `src/web/` - Frontend web application
- `src/spacelaunchnow/` - Django project configuration

### Notification System (`src/bot/`)
- **Firebase Integration**: Push notifications via `pyfcm` and service account credentials
- **Social Media**: Automated posting to Instagram/Twitter via Buffer API
- **Event-Driven**: Triggered by launch status changes and timing updates
- **Template Engine**: Dynamic content generation for different notification types

### Autoscaler (`src/autoscaler/`)
- **Predictive Scaling**: Analyzes upcoming launches and events for traffic prediction
- **DigitalOcean Integration**: Manages Kubernetes node pools via API
- **KEDA Support**: Horizontal pod autoscaling based on metrics
- **Logging**: Comprehensive debug logging for scaling decisions

## Development Workflows

### Setup and Dependencies
```bash
make setup           # Poetry deps + pre-commit hooks
poetry install --with dev
poetry run pre-commit install
```

### Local Development
```bash
make shell          # Django shell_plus with enhanced features
make build          # Build Docker containers
make local-test     # Run Django tests locally
make test           # Full Docker-based test suite
```

### Docker Environment
- `docker/docker-compose.yml` - Development stack
- `docker/docker-compose.test.yml` - Testing environment
- Shared volumes for live code reloading

## Key Patterns

### Settings Architecture
- Environment-based configuration in `src/spacelaunchnow/settings/`
- Uses `environs` for type-safe environment variable parsing
- Sentry integration for error tracking and performance monitoring
- Firebase credentials via JSON environment variables

### Model Integration
- Imports models from LaunchLibrary-API via shared packages
- Custom `base_models.py` for SpaceLaunchNow-specific extensions
- Shared caching strategy with django-cachalot

### Notification Pipeline
```python
# Event detection → Template selection → Multi-channel delivery
bot.app.notification_service.NotificationService()
# Handles FCM, social media, and web notifications
```

### Autoscaler Logic
```python
# Launch analysis → Traffic prediction → Node scaling
autoscaler.autoscaler.check_autoscaler()
# Weighs launch importance, timing, and historical patterns
```

## Deployment Integration

### Helm Chart Structure
Managed in SpaceLaunchNow-GitOps repository:
- `manifests/helm/spacelaunchnow/` - Main chart templates
- `manifests/apps/staging/` - Staging environment values
- `manifests/apps/production/` - Production environment values

### CI/CD Pipeline
- GitHub Actions build and push Docker images
- Automatic GitOps repository updates with new image tags
- ArgoCD-managed deployments to Kubernetes clusters

### Environment Management
- **Staging**: Auto-deployed from `main` branch
- **Production**: Manual approval workflow
- Environment-specific configurations via Helm values

## External Integrations

### Firebase Cloud Messaging
- Service account authentication via JSON credentials
- Multi-platform push notifications (iOS/Android)
- Topic-based subscription management

### DigitalOcean Kubernetes
- Node pool management via API
- Cost optimization through predictive scaling
- Integration with KEDA for workload-based scaling

### Buffer API
- Automated social media content scheduling
- Instagram and Twitter post management
- Launch announcement automation

## Important Files
- `src/manage.py` - Django management with custom commands
- `src/spacelaunchnow/settings/__init__.py` - Core configuration
- `src/bot/app/notification_service.py` - FCM integration
- `src/autoscaler/autoscaler.py` - Scaling logic
- `pyproject.toml` - Poetry dependencies and project metadata

## Development Tips
- Use `poetry shell` for isolated development environment
- Firebase credentials must be valid JSON in environment variables
- Autoscaler runs on scheduled tasks - check logs for scaling decisions
- Notification templates support dynamic content based on launch data
- Debug mode enables additional logging and disables external API calls
