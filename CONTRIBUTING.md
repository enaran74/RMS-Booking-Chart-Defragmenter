# Contributing to BookingChartDefragmenter

We welcome contributions to the BookingChartDefragmenter project! This document provides guidelines for contributing to the project.

## Table of Contents
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Submitting Changes](#submitting-changes)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/BookingChartDefragmenter.git
   cd BookingChartDefragmenter
   ```
3. **Add the original repository** as upstream:
   ```bash
   git remote add upstream https://github.com/original-owner/BookingChartDefragmenter.git
   ```

## Development Setup

1. **Install Python 3.7+** if not already installed
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables**:
   ```bash
   cp env.example .env
   # Edit .env with your development credentials
   ```
4. **Verify the setup**:
   ```bash
   python3 start.py --help
   ```

## Making Changes

### Before You Start
- Check the [issues](../../issues) to see if your idea is already being discussed
- For major changes, open an issue first to discuss your approach
- Keep your changes focused and atomic

### Branch Naming
Use descriptive branch names:
- `feature/add-new-analysis-metric`
- `bugfix/fix-email-attachment-issue`
- `improvement/optimize-caching-performance`
- `docs/update-installation-guide`

### Development Workflow
1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Make your changes** following the code style guidelines
3. **Test your changes** thoroughly
4. **Update documentation** if needed
5. **Commit your changes** with clear, descriptive messages

## Submitting Changes

### Pull Request Process
1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```
2. **Push your branch** to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Detailed description of what you changed and why
   - Reference to any related issues
   - Screenshots or examples if applicable

### Pull Request Checklist
- [ ] Code follows the project style guidelines
- [ ] Self-review of the code completed
- [ ] Commented code, particularly in hard-to-understand areas
- [ ] Documentation updated if needed
- [ ] No new warnings or errors introduced
- [ ] Tested with different configuration options
- [ ] Sensitive information removed (no hardcoded credentials)

## Code Style

### Python Style Guidelines
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use descriptive variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular
- Use type hints where appropriate

### File Organization
- Keep related functionality in appropriate modules
- Use clear, descriptive file and module names
- Maintain the existing project structure

### Comments and Documentation
- Write clear, concise comments
- Update docstrings when changing function behavior
- Keep README.md updated with new features
- Add inline comments for complex logic

## Testing

### Manual Testing
Before submitting changes, test your code with:
1. **Different property configurations**:
   ```bash
   python3 start.py -p SINGLE_PROPERTY --test-args
   python3 start.py -p PROP1,PROP2 --test-args
   python3 start.py -p ALL --test-args
   ```
2. **Different modes**:
   ```bash
   python3 start.py -t --test-args  # Training mode
   python3 start.py -e --test-args  # With emails
   ```
3. **Error conditions**:
   - Invalid credentials
   - Network connectivity issues
   - Invalid property codes

### Test Environment
- Use the training database (`-t` flag) for testing
- Never test with production data unless absolutely necessary
- Always use test email addresses when testing email functionality

## Documentation

### Code Documentation
- Add docstrings to new functions and classes
- Update existing docstrings if you change function behavior
- Use clear, descriptive variable names that reduce the need for comments

### User Documentation
- Update README.md for new features or changed usage
- Update env.example for new configuration options
- Add examples for new command-line options

### Developer Documentation
- Update DEVELOPER_README.md for architectural changes
- Document new modules or significant algorithm changes
- Add troubleshooting information for common issues

## Issue Reporting

When reporting issues, please include:
- **Environment details**: Python version, OS, dependencies
- **Steps to reproduce** the issue
- **Expected behavior** vs actual behavior
- **Error messages** or logs if applicable
- **Configuration** used (anonymized)

## Feature Requests

For feature requests, please:
- Check existing issues first
- Describe the problem you're trying to solve
- Explain why this feature would be useful
- Provide examples of how it would be used
- Consider the impact on existing functionality

## Questions and Support

- Check the [README.md](README.md) for usage instructions
- Check the [DEVELOPER_README.md](DEVELOPER_README.md) for technical details
- Search existing [issues](../../issues) for similar questions
- Open a new issue for questions not covered elsewhere

## License

By contributing to this project, you agree that your contributions will be licensed under the same [MIT License](LICENSE) that covers the project.

Thank you for contributing to BookingChartDefragmenter! 🎉
