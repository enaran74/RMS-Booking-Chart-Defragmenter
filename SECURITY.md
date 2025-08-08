# Security Policy

## Supported Versions

We actively support security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do NOT Create a Public Issue

**Please do not report security vulnerabilities through public GitHub issues.**

### 2. Contact Us Privately

Send security vulnerability reports to:
- **Email**: [Create a secure contact method]
- **Subject**: "SECURITY: BookingChartDefragmenter Vulnerability Report"

### 3. Include These Details

Please include as much information as possible:
- Type of vulnerability (e.g., SQL injection, credential exposure, etc.)
- Full paths of source files related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment and potential risks

### 4. Response Timeline

We will acknowledge receipt of your vulnerability report within **48 hours** and will strive to:
- Confirm the vulnerability within **7 days**
- Provide a security patch within **30 days** for critical vulnerabilities
- Keep you informed throughout the process

## Security Best Practices

### For Users
1. **Never commit credentials**: Always use environment variables or secure credential management
2. **Use strong passwords**: Ensure RMS API credentials are strong and unique
3. **Regular updates**: Keep the application and its dependencies updated
4. **Secure deployment**: Use proper security practices when deploying
5. **Network security**: Ensure secure network connections when using the application

### For Contributors
1. **Code review**: All code changes require review before merging
2. **Dependency scanning**: Regularly check for vulnerabilities in dependencies
3. **Input validation**: Always validate and sanitize user inputs
4. **Error handling**: Don't expose sensitive information in error messages
5. **Secure defaults**: Use secure configuration defaults

## Known Security Considerations

### Credential Management
- RMS API credentials are required for operation
- Credentials should be provided via environment variables or secure configuration
- Never hardcode credentials in source code
- Use the provided `.env.example` as a template

### Data Handling
- The application processes reservation and guest data
- All data transmission should use secure connections (HTTPS)
- Log files may contain sensitive information - handle appropriately
- Generated Excel files may contain guest information - secure accordingly

### Email Functionality
- Email functionality requires SMTP credentials
- Use app-specific passwords for Gmail integration
- Email attachments may contain sensitive business data
- Verify recipient addresses to prevent data leakage

### API Security
- RMS API authentication tokens have expiration times
- The application implements token refresh mechanisms
- API rate limiting is respected to prevent service disruption
- API endpoints are configurable for different environments

## Dependencies Security

We regularly monitor our dependencies for security vulnerabilities:

### Core Dependencies
- `pandas` - Data manipulation and analysis
- `openpyxl` - Excel file generation
- `requests` - HTTP library for API calls
- `numpy` - Numerical computing

### Security Practices
- Dependencies are pinned to specific versions in `requirements.txt`
- Regular security audits of dependencies
- Prompt updates for security-related dependency updates

## Deployment Security

### Docker Deployment
- Use official Python base images
- Don't include credentials in Docker images
- Use Docker secrets or environment variables for sensitive data
- Regularly update base images for security patches

### Environment Security
- Secure the host system where the application runs
- Use appropriate file permissions for configuration files
- Implement network security measures (firewalls, VPNs)
- Monitor application logs for suspicious activity

## Incident Response

In case of a security incident:

1. **Immediate Actions**
   - Isolate affected systems
   - Preserve evidence and logs
   - Assess the scope of the incident

2. **Communication**
   - Notify stakeholders appropriately
   - Prepare public communication if necessary
   - Coordinate with security teams

3. **Recovery**
   - Implement fixes and patches
   - Verify system integrity
   - Update security measures

4. **Post-Incident**
   - Conduct post-incident review
   - Update security policies
   - Improve detection and response capabilities

## Security Updates

Security updates will be:
- Released as soon as possible after vulnerability confirmation
- Clearly marked in release notes
- Communicated through appropriate channels
- Backward compatible when possible

## Contact Information

For security-related questions or concerns:
- Review this security policy
- Check existing security advisories
- Contact the development team through secure channels

---

*This security policy is subject to updates. Please check regularly for the latest version.*
