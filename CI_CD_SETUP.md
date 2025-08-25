# CI/CD Pipeline Setup Guide

This guide helps you configure the complete CI/CD pipeline for the RMS Booking Chart Defragmenter.

## 🚀 Quick Setup

### 1. Required GitHub Secrets

You **MUST** configure these secrets for the CI/CD pipeline to work:

| Secret | Purpose | How to Get |
|--------|---------|------------|
| `DOCKER_USERNAME` | Docker Hub username | Your Docker Hub username |
| `DOCKER_PASSWORD` | Docker Hub access token | Create in Docker Hub → Settings → Security |

### 2. Setting Up Docker Hub Access

#### Step 1: Create Docker Hub Access Token
1. Login to [Docker Hub](https://hub.docker.com)
2. Go to **Account Settings** → **Security**
3. Click **New Access Token**
4. **Name**: `GitHub Actions RMS Defragmenter`
5. **Permissions**: Read, Write, Delete
6. **Copy the token** (you won't see it again!)

#### Step 2: Add Secrets to GitHub
1. Go to your GitHub repository
2. **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add both secrets:
   ```
   Name: DOCKER_USERNAME
   Value: your-dockerhub-username
   
   Name: DOCKER_PASSWORD  
   Value: dckr_pat_your-access-token-here
   ```

### 3. Verify Setup

After adding secrets, push any change to trigger the CI pipeline:

```bash
git add .
git commit -m "test: trigger CI pipeline"
git push origin main
```

You should see three workflow runs in the **Actions** tab:
- ✅ **CI Pipeline** - Code quality and testing
- ✅ **Docker Build & Push** - Build and push to Docker Hub  
- ✅ **Security Scanning** - Security analysis

## 📋 What Each Workflow Does

### CI Pipeline (`ci.yml`)
**Triggers**: Every push and pull request

**Runs:**
- ✅ Code formatting checks (Black, isort)
- ✅ Linting (flake8, MyPy)
- ✅ Security scanning (Bandit, Safety)
- ✅ Unit tests with PostgreSQL
- ✅ Docker build validation
- ✅ Documentation quality checks

### Docker Build & Push (`docker-build.yml`)
**Triggers**: Push to main, version tags (v1.0.0, etc.)

**Runs:**
- ✅ Multi-platform Docker builds (AMD64, ARM64)
- ✅ Automatic versioning from Git tags
- ✅ Push to Docker Hub with proper tags
- ✅ Container security scanning
- ✅ Build validation tests

### Security Scanning (`security.yml`)
**Triggers**: Daily at 2 AM UTC, security file changes

**Runs:**
- ✅ Dependency vulnerability scanning
- ✅ Static code security analysis
- ✅ Secret detection (hardcoded passwords, etc.)
- ✅ Container image security scanning
- ✅ Comprehensive security reporting

## 🏷️ Version Management Integration

The CI/CD pipeline integrates with your Git-based versioning:

### Creating Releases
```bash
# Create a new release
git tag v2.2.0 -m "Release v2.2.0: New features"
git push origin v2.2.0
```

**This triggers:**
1. Full CI pipeline validation
2. Docker image build with version tags:
   - `enaran/rms-defragmenter:v2.2.0`
   - `enaran/rms-defragmenter:2.2.0`
   - `enaran/rms-defragmenter:2.2`
   - `enaran/rms-defragmenter:2`
   - `enaran/rms-defragmenter:latest`

### Development Builds
```bash
# Regular push to main
git push origin main
```

**This triggers:**
1. CI pipeline validation
2. Docker image build with development tags:
   - `enaran/rms-defragmenter:main`
   - `enaran/rms-defragmenter:latest`

## 🔍 Monitoring Your Pipeline

### 1. GitHub Actions Tab
- View all workflow runs and their status
- Click on any run to see detailed logs
- Download artifacts (security reports, build summaries)

### 2. Security Tab
- View vulnerability reports uploaded by Trivy
- See dependency security alerts
- Track security trends over time

### 3. Docker Hub
- Verify images are being pushed correctly
- Check image sizes and architecture support
- View download statistics

## 🛠️ Customization Options

### Changing Trigger Conditions
Edit workflow files in `.github/workflows/`:

```yaml
# Run CI on more branches
on:
  push:
    branches: [ main, develop, feature/* ]

# Change security scan schedule  
on:
  schedule:
    - cron: '0 6 * * *'  # 6 AM UTC instead of 2 AM
```

### Adding Notification Webhooks
Add Slack/Discord notifications:

```yaml
- name: Notify Slack
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Environment-Specific Deployments
Add staging deployments:

```yaml
- name: Deploy to staging
  if: github.ref == 'refs/heads/develop'
  run: |
    # Deploy to staging environment
    ./deploy-staging.sh
```

## 🚨 Troubleshooting

### Common Issues

**❌ "Docker login failed"**
- Check `DOCKER_USERNAME` and `DOCKER_PASSWORD` secrets
- Verify Docker Hub access token has correct permissions
- Ensure username matches exactly (case sensitive)

**❌ "Permission denied pushing to Docker Hub"**
- Verify access token has `Read, Write, Delete` permissions
- Check repository name `enaran/rms-defragmenter` exists
- Ensure you have push access to the repository

**❌ "Security scan failed"**
- Review Bandit configuration for false positives
- Check if new dependencies introduced vulnerabilities
- Verify all security tools can access required files

**❌ "Build timeout"**
- Optimize Dockerfile for faster builds
- Use Docker layer caching effectively
- Consider splitting large builds into stages

### Getting Help

1. **Check workflow logs** - Click on failed steps in Actions tab
2. **Review artifacts** - Download security reports for details
3. **Test locally** - Run Docker builds and security scans locally
4. **Check dependencies** - Ensure all required tools are available

## ✅ Success Indicators

When everything is working correctly, you should see:

### On Every Push:
- ✅ CI Pipeline completes successfully
- ✅ All code quality checks pass
- ✅ Security scans show no critical issues
- ✅ Docker builds complete without errors

### On Version Tags:
- ✅ Multi-platform images pushed to Docker Hub
- ✅ Proper version tags applied
- ✅ Container security validation passes
- ✅ Release artifacts generated

### Daily Security Scans:
- ✅ Dependency vulnerability checks complete
- ✅ No new security issues detected  
- ✅ Container images remain secure
- ✅ Security reports uploaded to GitHub

This pipeline ensures your code is always tested, secure, and ready for deployment! 🚀
