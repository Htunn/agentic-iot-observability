# Contributing to IoT Observability Project

Thank you for your interest in contributing to our IoT Observability Project! This document provides guidelines for contributing to maintain quality and security.

## Security Best Practices

When contributing, please follow these security best practices:

### General Guidelines

1. **Never commit secrets or credentials**
   - No API keys, passwords, or tokens in code
   - Use environment variables for configuration
   - Add sensitive files to .gitignore

2. **Input Validation**
   - Validate all inputs from untrusted sources
   - Use parameterized queries for database operations
   - Sanitize data displayed to users

3. **Dependency Management**
   - Pin dependency versions
   - Use only necessary dependencies
   - Regularly update dependencies for security patches

### Code Contributions

1. **Clean and Secure Code**
   - Follow PEP 8 guidelines for Python code
   - Include comprehensive error handling
   - Add proper logging (avoid logging sensitive data)
   - Add type hints to function signatures
   - Write docstrings for all functions and classes

2. **Docker Best Practices**
   - Use specific version tags for base images (not 'latest')
   - Use minimal base images where possible
   - Run containers as non-root users
   - Remove unnecessary tools and packages
   - Implement proper health checks

3. **Testing Requirements**
   - Add appropriate unit tests for new features
   - Include security-focused test cases
   - Document test procedures

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Update documentation as needed
6. Commit with clear, descriptive messages
7. Push to your branch
8. Submit a Pull Request

## Code Review Process

All submissions will be reviewed for:

1. Functionality: Does it work as intended?
2. Security: Does it follow security best practices?
3. Code quality: Is it well-written and maintainable?
4. Documentation: Is it properly documented?

## Reporting Security Issues

If you discover a security vulnerability, please do NOT open a public issue.
Instead, email us at [security@example.com](mailto:security@example.com).

Thank you for helping to keep this project secure!
