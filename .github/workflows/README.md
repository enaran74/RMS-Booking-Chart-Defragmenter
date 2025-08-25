# CI/CD Pipeline Documentation

This directory contains GitHub Actions workflows for automated testing, security scanning, and deployment of the RMS Booking Chart Defragmenter.

## 🔄 Workflows Overview

### 1. **CI Pipeline** (`ci.yml`)

**Triggers:** Push to main/develop, Pull Requests, Manual dispatch

**Jobs:**

- **Code Quality & Security**: Linting, formatting, security scans
- **Unit Tests**: Automated testing with PostgreSQL
- **Build Validation**: Docker build verification
- **Documentation Quality**: Markdown linting and structure validation

**Features:**

- Python code quality checks (Black, isort, flake8, MyPy)
- Security scanning (Bandit, Safety)
- Import validation and basic functionality tests
- Docker build validation without pushing
- Markdown documentation quality checks

### 2. **Docker Build & Push** (`docker-build.yml`)

**Triggers:** Version tags (v*), Main branch pushes, Manual dispatch

**Jobs:**

- **Build & Push**: Multi-platform Docker image build and push
- **Security Scan**: Container vulnerability scanning with Trivy
- **Notify Success**: Build completion notifications

**Features:**

- Multi-platform builds (linux/amd64, linux/arm64)
- Automatic version extraction from Git tags
- Docker Hub integration with proper tagging
- Container security scanning
- Build artifact validation

### 3. **Security Scanning** (`security.yml`)
**Triggers:** Daily schedule (2 AM UTC), Security-related file changes, Manual dispatch

**Jobs:**
- **Dependency Scan**: Vulnerability scanning of Python dependencies
- **Code Security**: Static code analysis with Bandit
- **Secrets Detection**: TruffleHog and pattern-based secret detection
- **Container Security**: Image vulnerability scanning
- **Security Summary**: Consolidated security reporting

**Features:**
- Daily automated security scans
- Multiple security tools integration
- Comprehensive reporting with GitHub Security tab integration
- Artifact retention for security reports

## 🔐 Required GitHub Secrets

To use these workflows, configure the following secrets in your GitHub repository:

### Repository Secrets (Settings → Secrets and variables → Actions)

| Secret Name | Description | Required For | Example |
|-------------|-------------|--------------|---------|
| `DOCKER_USERNAME` | Docker Hub username | Docker builds | `dhpsystems` |
| `DOCKER_PASSWORD` | Docker Hub access token | Docker builds | `dckr_pat_...` |

### Setting Up Docker Hub Secrets

1. **Create Docker Hub Access Token:**
   ```bash
   # Login to Docker Hub
   # Go to Account Settings → Security → New Access Token
   # Name: "GitHub Actions RMS Defragmenter"
   # Permissions: Read, Write, Delete
   ```

2. **Add to GitHub Secrets:**
   ```bash
   # Repository Settings → Secrets and variables → Actions → New repository secret
   DOCKER_USERNAME: your-dockerhub-username
   DOCKER_PASSWORD: your-access-token
   ```

## 🚀 Workflow Behavior

### On Pull Requests
- ✅ Full CI pipeline runs (testing, linting, security)
- ✅ Docker build validation (no push)
- ✅ Security scanning for changed files
- ❌ No Docker Hub pushes
- ❌ No container security scans

### On Main Branch Push
- ✅ Full CI pipeline
- ✅ Docker build and push to `latest` tag
- ✅ Container security scanning
- ✅ Success notifications

### On Version Tags (v1.0.0, v2.1.0, etc.)
- ✅ Full CI pipeline
- ✅ Docker build and push with version tags
- ✅ Multi-platform builds
- ✅ Release-specific tagging

### Daily Schedule
- ✅ Complete security scanning
- ✅ Dependency vulnerability checks
- ✅ Container image security validation
- ✅ Security report generation

## 📊 Monitoring & Reports

### GitHub Actions Tab
- View workflow runs and status
- Download build artifacts
- Review job logs and timings

### Security Tab
- SARIF vulnerability reports
- Container security findings
- Dependency vulnerability alerts

### Artifacts
- Security scan reports (JSON format)
- Build summaries and metadata
- Test results and coverage reports

## 🛠️ Customization

### Modifying Triggers
Edit the `on:` section in each workflow file:

```yaml
on:
  push:
    branches: [ main, develop, feature/* ]  # Add more branches
  schedule:
    - cron: '0 6 * * *'  # Change schedule time
```

### Adding New Security Tools
Extend the security workflow with additional scanners:

```yaml
- name: Custom security tool
  run: |
    # Install and run your security tool
    custom-scanner --output results.json
```

### Environment-Specific Builds
Add environment-specific Docker builds:

```yaml
- name: Build staging image
  if: github.ref == 'refs/heads/develop'
  uses: docker/build-push-action@v5
  with:
    tags: ${{ env.IMAGE_NAME }}:staging
```

## 🔧 Troubleshooting

### Common Issues

**1. Docker Hub Authentication Fails**
```bash
Error: buildx failed with: ERROR: failed to solve: failed to authorize
```
**Solution:** Verify `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets are correct

**2. Security Scans Fail**
```bash
Error: Bandit security scan failed
```
**Solution:** Review Bandit configuration in `.bandit` file, exclude false positives

**3. Build Timeouts**
```bash
Error: The job running on runner GitHub Actions X has exceeded the maximum execution time
```
**Solution:** Optimize Dockerfile, use multi-stage builds, leverage build cache

### Debugging Steps

1. **Check workflow logs** in GitHub Actions tab
2. **Verify secrets** are properly configured
3. **Test locally** using `act` or manual Docker commands
4. **Review artifact uploads** for detailed error reports

## 📝 Maintenance

### Regular Tasks
- **Monthly**: Review and update action versions (@v4 → @v5)
- **Quarterly**: Update security scanning tools and configurations
- **As needed**: Adjust triggers and notification settings

### Updating Actions
```bash
# Check for newer action versions
grep -r "uses:.*@v" .github/workflows/
# Update version numbers in workflow files
```

This CI/CD pipeline provides comprehensive automation while maintaining security best practices. All sensitive data is properly managed through GitHub Secrets, and the workflows are designed to fail safely without exposing credentials.
