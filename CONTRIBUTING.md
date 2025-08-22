# Contributing to RMS Booking Chart Defragmenter

We welcome contributions to the RMS Booking Chart Defragmenter project! This document provides guidelines for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Production Pipeline](#production-pipeline)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/RMS-Booking-Chart-Defragmenter.git
   cd RMS-Booking-Chart-Defragmenter
   ```
3. **Add the original repository** as upstream:
   ```bash
   git remote add upstream https://github.com/enaran74/RMS-Booking-Chart-Defragmenter.git
   ```

## Development Setup

### Option 1: Local Development (Recommended for Code Changes)

1. **Install Python 3.11+** if not already installed
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   cd web_app && pip install -r requirements.txt
   ```
3. **Set up environment variables**:
   ```bash
   cp env.example .env.dev
   # Edit .env.dev with your development credentials
   ```
4. **Start PostgreSQL** (for web app development):
   ```bash
   docker run -d --name dev-postgres \
     -e POSTGRES_DB=defrag_db \
     -e POSTGRES_USER=defrag_user \
     -e POSTGRES_PASSWORD=DefragDB2024! \
     -p 5432:5432 postgres:15-alpine
   ```
5. **Verify the setup**:
   ```bash
   python3 start.py --help
   cd web_app && uvicorn main:app --reload
   ```

### Option 2: Docker Development

1. **Use customer installation for testing**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/enaran74/RMS-Booking-Chart-Defragmenter/main/install-customer.sh | bash
   ```
2. **Mount your development code**:
   ```bash
   # Add volume mounts to docker-compose.yml for development
   volumes:
     - ./web_app:/app/web_app
     - ./defrag_analyzer.py:/app/defrag_analyzer.py
   ```

## Making Changes

### Before You Start
- Check the [issues](../../issues) to see if your idea is already being discussed
- For major changes, open an issue first to discuss your approach
- Keep your changes focused and atomic
- Understand the [production pipeline](#production-pipeline)

### Branch Naming
Use descriptive branch names:
- `feature/add-new-analysis-metric`
- `bugfix/fix-email-attachment-issue`
- `improvement/optimize-caching-performance`
- `docs/update-installation-guide`
- `deployment/improve-docker-build`

### Development Workflow
1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** following the code style guidelines
3. **Test your changes** thoroughly (see [Testing](#testing))
4. **Update documentation** if needed
5. **Commit your changes** with clear, descriptive messages

### Key Components to Understand

#### Web Application (`web_app/`)
- **FastAPI backend** with PostgreSQL database
- **Authentication system** with JWT tokens
- **Real-time WebSocket** communication
- **RESTful API** for all operations

#### CLI Analyzer (Root directory)
- **Core defragmentation logic** in `defrag_analyzer.py`
- **RMS API client** in `rms_client.py`
- **Excel report generation** in `excel_generator.py`
- **Email notifications** in `email_sender.py`

#### Production Pipeline
- **Multi-stage Docker builds** for optimized images
- **Pre-built images** on Docker Hub
- **Smart customer installer** with environment detection
- **Multi-architecture support** (AMD64, ARM64)

## Submitting Changes

### Pull Request Process
1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. **Test with production pipeline** if applicable:
   ```bash
   # Test Docker build
   docker build -f Dockerfile.production -t test-image .
   
   # Test customer installation
   ./install-customer.sh
   ```
3. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
4. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what you changed and why
   - Reference to any related issues
   - Screenshots or examples if applicable
   - Testing instructions

### Pull Request Checklist
- [ ] Code follows the project style guidelines
- [ ] Self-review of the code completed
- [ ] Commented code, particularly in hard-to-understand areas
- [ ] Documentation updated if needed
- [ ] No new warnings or errors introduced
- [ ] Tested with different configuration options
- [ ] Sensitive information removed (no hardcoded credentials)
- [ ] Docker builds successfully (if changes affect Docker)
- [ ] Customer installation tested (if changes affect deployment)

## Code Style

### Python Style Guidelines
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Use type hints where appropriate

### File Organization
- **CLI Code**: Root directory for analysis logic
- **Web App**: `web_app/` directory for web interface
- **Shared Code**: Use imports to share common functionality
- **Docker**: Separate Dockerfiles for different purposes
- **Documentation**: Update relevant `.md` files

### Comments and Documentation
- Write clear, concise comments
- Update docstrings when changing function behavior
- Keep README.md updated with new features
- Add inline comments for complex logic
- Update `DEPLOYMENT.md` for deployment changes

## Testing

### Manual Testing

#### Web Application Testing
```bash
# Start development server
cd web_app
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

#### CLI Testing
```bash
# Test with training database
python3 start.py -t -p SADE --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD"

# Test different property configurations
python3 start.py -t -p ALL --agent-id $AGENT_ID --agent-password "$AGENT_PASSWORD" \
  --client-id $CLIENT_ID --client-password "$CLIENT_PASSWORD"
```

#### Docker Testing
```bash
# Test production build
docker build -f Dockerfile.production -t test-build .

# Test customer installation
./install-customer.sh

# Test in different environments
docker run --rm --network host test-build
```

### Integration Testing

#### End-to-End Testing
1. **Install via customer script**:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/your-fork/RMS-Booking-Chart-Defragmenter/your-branch/install-customer.sh | bash
   ```
2. **Configure with test credentials**
3. **Run full analysis cycle**
4. **Verify web interface functionality**
5. **Check log outputs**

#### Environment Testing
- **Standard deployment**: Test with `docker-compose.customer.yml`
- **Host networking**: Test with `docker-compose.hostnet.yml`  
- **Multi-architecture**: Test on different platforms if possible

### Test Environment
- Use the training database (`USE_TRAINING_DB=true`) for testing
- Never test with production data unless absolutely necessary
- Always use test email addresses when testing email functionality
- Use temporary Docker containers that can be easily removed

## Documentation

### Code Documentation
- Add docstrings to new functions and classes
- Update existing docstrings if you change function behavior
- Use clear, descriptive variable names that reduce the need for comments

### User Documentation
- Update `README.md` for new features or changed usage
- Update `env.example` for new configuration options
- Add examples for new command-line options
- Update `SCRIPTS.md` for new management scripts

### Developer Documentation
- Update `DEVELOPER_README.md` for architectural changes
- Update `DEPLOYMENT.md` for deployment pipeline changes
- Document new modules or significant algorithm changes
- Add troubleshooting information for common issues

## Production Pipeline

### Understanding the Pipeline

#### Developer Workflow
1. **Code changes** → Local testing
2. **Build production images** → `./build-pipeline.sh`
3. **Push to Docker Hub** → Automated via build script
4. **Test customer deployment** → Use install-customer.sh
5. **Create pull request** → With testing documentation

#### Customer Workflow
1. **One-command installation** → `curl ... | bash`
2. **Smart environment detection** → Automatic networking setup
3. **Pre-built image download** → No compilation required
4. **Configuration** → Edit `.env` file
5. **Management** → Use provided scripts

### Contributing to the Pipeline

#### Docker Improvements
- **Optimize build time**: Multi-stage builds, layer caching
- **Reduce image size**: Minimal dependencies, cleanup steps
- **Improve security**: Non-root users, minimal attack surface
- **Add health checks**: Container and application health

#### Installation Improvements
- **Better error handling**: Clear error messages and recovery
- **More environment detection**: Additional networking scenarios
- **Platform support**: New architectures or operating systems
- **Configuration validation**: Better credential checking

#### Management Scripts
- **Enhanced monitoring**: Better health checks and diagnostics
- **Automated backup**: Data backup and recovery procedures
- **Performance monitoring**: Resource usage tracking
- **Log management**: Rotation and archival strategies

### Testing Pipeline Changes

#### Before Submitting
1. **Test locally**: Build and run images locally
2. **Test installation**: Run customer installation script
3. **Test different environments**: Various networking scenarios
4. **Verify documentation**: Ensure all docs are updated

#### In Pull Request
1. **Describe changes**: What was changed and why
2. **Testing instructions**: How reviewers can test
3. **Migration notes**: Any breaking changes or migration steps
4. **Performance impact**: Any performance implications

## Issue Reporting

When reporting issues, please include:
- **Environment details**: Docker version, OS, architecture
- **Installation method**: Customer script vs manual vs development
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Error messages** or logs if applicable
- **Configuration** used (anonymized)
- **Networking setup**: VPN, Tailscale, special configurations

## Feature Requests

For feature requests, please:
- Check existing issues first
- Describe the problem you're trying to solve
- Explain why this feature would be useful
- Provide examples of how it would be used
- Consider the impact on existing functionality
- Think about deployment and customer impact

## Questions and Support

- Check the [README.md](README.md) for usage instructions
- Check the [DEPLOYMENT.md](DEPLOYMENT.md) for deployment details
- Check the [DEVELOPER_README.md](DEVELOPER_README.md) for technical details
- Search existing [issues](../../issues) for similar questions
- Open a new issue for questions not covered elsewhere

## Release Process

### For Maintainers

#### Minor Updates
1. **Merge pull request** to main branch
2. **Build and push images**: `./build-pipeline.sh`
3. **Test customer installation** with new images
4. **Update documentation** if needed

#### Major Releases
1. **Create release branch**: `release/v2.1.0`
2. **Update version numbers** in relevant files
3. **Build and tag images**: Include version tags
4. **Comprehensive testing**: Full deployment testing
5. **Create GitHub release**: With changelog and notes
6. **Update installation URLs**: If installation script changed

## License

By contributing to this project, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

Thank you for contributing to the RMS Booking Chart Defragmenter! 🎉

Your contributions help improve accommodation optimization for Discovery Holiday Parks and make the system more reliable for all users.