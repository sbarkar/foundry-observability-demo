# Contributing to Azure Foundry Observability Demo

Thank you for your interest in contributing to this project! This document provides guidelines for contributing.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Before creating an issue, check if one already exists
- Include detailed information:
  - Steps to reproduce
  - Expected behavior
  - Actual behavior
  - Environment details (OS, Python version, Azure region, etc.)
  - Logs and error messages

### Suggesting Enhancements

- Use GitHub issues to suggest enhancements
- Clearly describe the feature and its benefits
- Provide examples of how it would work

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test your changes thoroughly
5. Commit with clear messages: `git commit -m 'Add amazing feature'`
6. Push to your fork: `git push origin feature/amazing-feature`
7. Open a Pull Request

## Development Guidelines

### Code Style

**Python:**
- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings for functions and classes
- Keep functions focused and small

**JavaScript:**
- Use ES6+ features
- Use meaningful variable names
- Add comments for complex logic
- Keep functions pure when possible

**Bicep:**
- Use meaningful resource names
- Add descriptions for parameters
- Follow Azure naming conventions
- Group related resources

### Testing

- Add tests for new features
- Ensure existing tests pass
- Test locally before submitting PR
- Include both unit and integration tests where applicable

### Documentation

- Update README.md for significant changes
- Add inline comments for complex code
- Update DEPLOYMENT.md if deployment steps change
- Include examples in documentation

### Security

- Never commit secrets or credentials
- Use environment variables for configuration
- Follow Azure security best practices
- Report security vulnerabilities privately

## Development Setup

### Prerequisites

- Python 3.11+
- Azure Functions Core Tools v4
- Azure CLI
- Git

### Local Setup

```bash
# Clone repository
git clone https://github.com/sbarkar/foundry-observability-demo.git
cd foundry-observability-demo

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your values

# Start backend
func start

# In another terminal, frontend setup
cd ../frontend
# Edit config.js with your values
python -m http.server 8080
```

### Making Changes

1. Create a new branch for your feature
2. Make your changes
3. Test locally
4. Commit with clear messages
5. Push and create a PR

### Commit Messages

Use clear, descriptive commit messages:

- `feat: Add new chat feature`
- `fix: Resolve authentication bug`
- `docs: Update deployment guide`
- `refactor: Improve error handling`
- `test: Add integration tests`

## Code Review Process

1. Maintainers will review your PR
2. Address any feedback or requested changes
3. Once approved, your PR will be merged
4. Your contribution will be acknowledged

## Community Guidelines

- Be respectful and inclusive
- Help others learn and grow
- Give constructive feedback
- Follow the Code of Conduct

## Questions?

- Open an issue for questions
- Tag maintainers if needed
- Check existing documentation first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be acknowledged in the project documentation.

Thank you for contributing! 🎉
