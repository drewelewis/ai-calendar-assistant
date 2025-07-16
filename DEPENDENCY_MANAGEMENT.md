# Dependency Management Guide

## Overview

This project now uses pinned versions to prevent dependency drift and ensure reproducible builds across all environments.

## File Structure

- **`requirements.txt`** - Production dependencies with exact versions
- **`requirements-dev.txt`** - Additional development/testing dependencies  
- **`requirements-lock.txt`** - Complete lock file with ALL packages (including transitive dependencies)

## Installation Instructions

### Production Deployment
```bash
pip install -r requirements.txt
```

### Development Environment
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Exact Environment Reproduction
```bash
pip install -r requirements-lock.txt
```

## Updating Dependencies

### 1. Minor Updates (Patch Versions)
For security fixes and bug fixes, update patch versions:
```bash
# Example: Update from 1.2.3 to 1.2.4
pip install --upgrade package-name
pip freeze > requirements-lock.txt
```

### 2. Major Updates (Requires Testing)
For major version updates:
1. Create a test environment
2. Update one package at a time
3. Run full test suite
4. Update requirements.txt with new version
5. Regenerate lock file

### 3. Security Updates
Monitor for security advisories:
```bash
pip audit  # Check for known vulnerabilities
```

## Dependency Categories

### Core Framework
- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### AI/ML Stack
- **OpenAI**: AI model access
- **Semantic Kernel**: AI orchestration framework

### Azure Integration
- **Azure SDK**: Cloud services integration
- **Microsoft Graph**: Office 365 integration
- **Azure Monitor**: Telemetry and monitoring

### Observability
- **OpenTelemetry**: Distributed tracing and metrics
- **Azure Monitor**: Production monitoring

## Best Practices

1. **Always pin versions** in requirements.txt
2. **Test updates** in staging before production
3. **Keep security patches current** 
4. **Review dependency licenses** before adding new packages
5. **Monitor for vulnerabilities** regularly
6. **Backup working environment** before major updates

## Troubleshooting

### Dependency Conflicts
```bash
pip-tools compile requirements.in  # If using pip-tools
pip check  # Check for dependency conflicts
```

### Version Rollback
```bash
pip install -r requirements-lock.txt --force-reinstall
```

### Clean Installation
```bash
pip uninstall -r requirements.txt -y
pip install -r requirements.txt
```

## Security Considerations

- **Pin exact versions** to prevent supply chain attacks
- **Regular security audits** of dependencies
- **Monitor CVE databases** for known vulnerabilities
- **Use virtual environments** to isolate dependencies
- **Review new packages** before adding to requirements

## Automation

Consider setting up:
- **Dependabot** for automated security updates
- **CI/CD tests** for dependency updates
- **Regular security scans** in deployment pipeline

---
**Last Updated**: 2025-07-16  
**Python Version**: 3.13.5
