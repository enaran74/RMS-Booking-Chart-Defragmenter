# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          | Notes |
| ------- | ------------------ | ----- |
| 2.0+    | :white_check_mark: | Production pipeline with pre-built images |
| < 2.0   | :x:                | Legacy versions, upgrade recommended |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT Create a Public Issue

**Please do not report security vulnerabilities through public GitHub issues.**

### 2. Contact Us Privately

Send security vulnerability reports to:
- **GitHub Security**: Use GitHub's security advisory feature
- **Email**: Create a secure contact through GitHub
- **Subject**: "SECURITY: RMS Defragmenter Vulnerability Report"

### 3. Include These Details

Please include as much information as possible:
- Type of vulnerability (e.g., SQL injection, credential exposure, container escape)
- Full paths of source files related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment and potential risks
- Affected deployment methods (Docker, local installation, etc.)

### 4. Response Timeline

We will acknowledge receipt of your vulnerability report within **48 hours** and will strive to:
- Confirm the vulnerability within **7 days**
- Provide a security patch within **30 days** for critical vulnerabilities
- Update Docker images and deployment pipeline as needed
- Keep you informed throughout the process

## Security Best Practices

### For Customers/Users

#### Deployment Security
1. **Use official images**: Only use images from `dhpsystems/rms-defragmenter`
2. **Verify image integrity**: Check image signatures when available
3. **Regular updates**: Use `./update.sh` to keep system current
4. **Secure host**: Ensure Docker host is properly secured
5. **Network security**: Use firewalls and VPNs appropriately

#### Credential Management
1. **Never commit credentials**: Always use environment variables
2. **Use strong passwords**: Ensure RMS API credentials are strong and unique
3. **Rotate credentials**: Regularly update API passwords
4. **Secure .env files**: Protect configuration files with proper permissions
5. **Monitor access**: Track who has access to credentials

#### Container Security
1. **Resource limits**: Docker containers have built-in resource limits
2. **Non-root execution**: Containers run as non-root user
3. **Network isolation**: Use appropriate Docker networking
4. **Volume security**: Secure mounted volumes and data

### For Contributors/Developers

#### Code Security
1. **Code review**: All code changes require review before merging
2. **Dependency scanning**: Regularly check for vulnerabilities in dependencies
3. **Input validation**: Always validate and sanitize user inputs
4. **Error handling**: Don't expose sensitive information in error messages
5. **Secure defaults**: Use secure configuration defaults

#### Docker Security
1. **Multi-stage builds**: Use production Dockerfile with minimal attack surface
2. **Base image security**: Regularly update base images
3. **Secret management**: Never include secrets in Docker images
4. **Layer optimization**: Minimize layers and clean up artifacts
5. **Security scanning**: Scan images for vulnerabilities

## Known Security Considerations

### Production Pipeline Security

#### Pre-Built Images
- **Image source**: Images built from verified source code
- **Multi-architecture**: Support for AMD64, ARM64 architectures
- **Minimal surface**: Production images contain only necessary components
- **Non-root user**: Containers run as `appuser`, not root
- **Health checks**: Built-in health monitoring for early issue detection

#### Build Pipeline
- **Secure build environment**: Images built in controlled environment
- **Dependency verification**: All dependencies from trusted sources
- **Automated testing**: Images tested before publication
- **Version control**: All image versions tracked and auditable

### Credential Management

#### RMS API Credentials
- **Environment variables**: Credentials provided via environment variables only
- **Configuration files**: Stored in `.env` files with proper permissions
- **No hardcoding**: Never embedded in source code or Docker images
- **Secure transmission**: All API calls use HTTPS
- **Token management**: Automatic token refresh and expiration handling

#### Web Application Security
- **JWT tokens**: Secure token-based authentication
- **Password hashing**: User passwords properly hashed with bcrypt
- **Session management**: Secure session handling
- **CORS protection**: Appropriate cross-origin request handling
- **SQL injection protection**: Parameterized queries and input validation

### Data Handling

#### Sensitive Data Processing
- **Guest information**: Reservation data handled securely
- **PCI compliance**: No payment card data processed
- **Data encryption**: Sensitive data encrypted in transit
- **Log sanitization**: No sensitive data in log files
- **Temporary files**: Secure handling of temporary analysis files

#### Database Security
- **PostgreSQL**: Industry-standard database with security features
- **User isolation**: Dedicated database user with minimal privileges
- **Network isolation**: Database accessible only within Docker network
- **Backup security**: Database backups handled securely
- **Connection encryption**: Encrypted database connections

### Network Security

#### Docker Networking
- **Bridge networking**: Default secure Docker networking
- **Host networking**: Available for environments with conflicts
- **Port isolation**: Only necessary ports exposed
- **Internal communication**: Secure inter-container communication
- **Firewall integration**: Compatible with host firewall rules

#### API Security
- **HTTPS enforcement**: All external API calls use HTTPS
- **Rate limiting**: Built-in rate limiting for RMS API
- **Authentication headers**: Secure token handling
- **Certificate validation**: Proper SSL certificate validation
- **Network timeouts**: Appropriate timeout handling

## Dependencies Security

We regularly monitor our dependencies for security vulnerabilities:

### Core Dependencies
- **Python 3.11+**: Latest stable Python version
- **FastAPI**: Modern web framework with security features
- **PostgreSQL**: Secure database system
- **Docker**: Containerization with security isolation

### Web Application Dependencies
- **SQLAlchemy**: ORM with SQL injection protection
- **Pydantic**: Data validation and settings management
- **PyJWT**: JWT token handling with cryptographic security
- **passlib**: Password hashing utilities
- **uvicorn**: ASGI server with security features

### Analysis Dependencies
- **pandas**: Data manipulation library
- **requests**: HTTP library with security features
- **openpyxl**: Excel file generation
- **numpy**: Numerical computing

### Security Practices
- **Version pinning**: Dependencies pinned to specific secure versions
- **Regular audits**: Automated security scanning of dependencies
- **Prompt updates**: Quick updates for security-related issues
- **Minimal dependencies**: Only necessary dependencies included

## Deployment Security

### Docker Container Security

#### Image Security
- **Official base images**: Built from official Python images
- **Multi-stage builds**: Separate build and runtime environments
- **Minimal runtime**: Only necessary runtime components
- **Regular updates**: Base images updated for security patches
- **Vulnerability scanning**: Images scanned for known vulnerabilities

#### Runtime Security
- **Non-root user**: Containers run as `appuser` (UID 1000)
- **Resource limits**: CPU and memory limits configured
- **Read-only filesystem**: Where possible, use read-only filesystems
- **Capability dropping**: Unnecessary Linux capabilities removed
- **Secrets management**: Secrets provided via environment variables

### Host Security

#### Docker Host
- **OS security**: Keep host operating system updated
- **Docker daemon**: Secure Docker daemon configuration
- **User permissions**: Proper user and group management
- **Network security**: Host-level firewall configuration
- **Log monitoring**: Monitor Docker and application logs

#### File System Security
- **Configuration files**: Proper permissions for `.env` files (600)
- **Log files**: Secure log file permissions and rotation
- **Volume mounts**: Secure Docker volume permissions
- **Backup security**: Secure backup storage and access
- **Data retention**: Appropriate data retention policies

### Network Security

#### Production Deployment
- **Reverse proxy**: Use nginx or similar for SSL termination
- **SSL certificates**: Valid SSL certificates for HTTPS
- **Network segmentation**: Isolate application network
- **VPN access**: Secure remote access methods
- **Monitoring**: Network traffic monitoring and alerting

## Incident Response

### Immediate Response

In case of a security incident:

1. **Containment**
   - Stop affected containers: `./stop.sh`
   - Isolate affected systems from network
   - Preserve evidence and logs for analysis
   - Assess scope and impact of incident

2. **Assessment**
   - Determine what data may have been compromised
   - Identify attack vectors and vulnerabilities
   - Assess business impact and regulatory requirements
   - Document all findings and actions taken

3. **Communication**
   - Notify stakeholders according to incident response plan
   - Prepare external communications if necessary
   - Coordinate with security teams and law enforcement if required
   - Maintain transparency while protecting sensitive information

### Recovery Process

1. **Immediate Actions**
   - Apply security patches or updates
   - Update Docker images: `./update.sh`
   - Rotate compromised credentials
   - Verify system integrity and functionality

2. **System Restoration**
   - Rebuild systems from clean backups if necessary
   - Verify all security measures are in place
   - Test all functionality before returning to service
   - Monitor systems closely for any suspicious activity

3. **Post-Incident Review**
   - Conduct thorough post-incident analysis
   - Update security policies and procedures
   - Improve detection and response capabilities
   - Share lessons learned with development team

## Security Updates

### Update Process

Security updates will be:
- **Released immediately**: Critical vulnerabilities addressed ASAP
- **Docker images updated**: New secure images pushed to Docker Hub
- **Customer notification**: Security updates communicated clearly
- **Backward compatible**: When possible, maintain compatibility
- **Well documented**: Clear upgrade instructions provided

### Customer Update Process

1. **Notification**: Security updates announced through appropriate channels
2. **Update command**: Customers can update with `./update.sh`
3. **Verification**: Verify update success with `./status.sh`
4. **Support**: Technical support available during updates

## Security Monitoring

### Automated Monitoring

#### Container Monitoring
- **Health checks**: Built-in Docker health checks
- **Resource monitoring**: CPU, memory, and disk usage
- **Log monitoring**: Application and system log analysis
- **Performance monitoring**: Response time and error rate tracking

#### Security Monitoring
- **Vulnerability scanning**: Regular image vulnerability scans
- **Dependency monitoring**: Automated dependency vulnerability checks
- **Access monitoring**: Authentication and authorization monitoring
- **Network monitoring**: Unusual network activity detection

### Manual Monitoring

#### Regular Reviews
- **Security configuration review**: Quarterly security settings review
- **Access review**: Regular review of user access and permissions
- **Log analysis**: Manual review of security-relevant logs
- **Penetration testing**: Periodic security testing

## Contact Information

For security-related questions or concerns:
- Review this security policy first
- Check existing security advisories in GitHub
- Use GitHub's security advisory feature for vulnerabilities
- Contact the development team through secure channels

### Emergency Contacts

For critical security incidents:
- **GitHub Security**: Use GitHub's private vulnerability reporting
- **Project Maintainers**: Contact through GitHub with "URGENT SECURITY" prefix

## Compliance Considerations

### Data Protection
- **GDPR compliance**: European data protection regulations
- **Privacy by design**: Privacy considerations built into system design
- **Data minimization**: Only collect and process necessary data
- **Data retention**: Appropriate data retention and deletion policies

### Industry Standards
- **OWASP guidelines**: Follow OWASP security best practices
- **Docker security**: Follow Docker security best practices
- **Container security**: Follow container security guidelines
- **API security**: Follow REST API security best practices

---

*This security policy is regularly updated to reflect current security practices and threat landscape. Please check regularly for the latest version.*

**Last updated**: 2025-01-22  
**Version**: 2.0