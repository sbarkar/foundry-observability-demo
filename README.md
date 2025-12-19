# Foundry Observability Demo

A repository showcasing an example of how to use Microsoft Foundry to deploy a simple and compliant GenAI use case using Microsoft native tools.

## Architecture

This project demonstrates a full-stack observability solution with:

- **Frontend** (`web/`): User interface for interacting with the GenAI application
- **Backend** (`api/`): Azure Functions-based API layer for handling requests
- **Infrastructure** (`infra/`): Bicep templates for Azure resource deployment
- **Documentation** (`docs/`): Additional project documentation

## Repository Structure

```
foundry-observability-demo/
├── web/              # Frontend application
├── api/              # Azure Functions backend
├── infra/            # Bicep infrastructure templates
├── docs/             # Documentation
├── .gitignore        # Git ignore patterns
├── pyproject.toml    # Python linting configuration
└── README.md         # This file
```

## Development Conventions

### Code Style

**Python (API)**
- Use Python 3.11+
- Follow PEP 8 style guide
- Use `ruff` for linting and `black` for code formatting
- Line length: 88 characters

**JavaScript/TypeScript (Frontend)**
- Use ESLint for linting
- Use Prettier for code formatting
- Single quotes for strings
- 2-space indentation
- Semicolons required

### Linting

**Python**
```bash
# Run ruff linter
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code with black
black .
```

**Frontend**
```bash
cd web/

# Run ESLint
npm run lint

# Auto-fix ESLint issues
npm run lint:fix

# Format with Prettier
npm run format

# Check formatting
npm run format:check
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Azure Functions Core Tools
- Azure CLI (for deployment)

### Backend (Azure Functions)

1. Navigate to the API directory:
   ```bash
   cd api/
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example settings file:
   ```bash
   cp local.settings.example.json local.settings.json
   ```

5. Update `local.settings.json` with your configuration (do not commit this file)

6. Run the Azure Functions locally:
   ```bash
   func start
   ```

The API will be available at `http://localhost:7071`

### Frontend

1. Navigate to the web directory:
   ```bash
   cd web/
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

## Configuration

### API Configuration

Configure the Azure Functions backend by creating a `local.settings.json` file in the `api/` directory. Use `local.settings.example.json` as a template.

**Never commit `local.settings.json` to version control** - it may contain secrets.

### Environment Variables

Key environment variables (set in `local.settings.json` for local development):

- `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint URL
- `AZURE_OPENAI_API_VERSION`: API version for Azure OpenAI
- `APPLICATIONINSIGHTS_CONNECTION_STRING`: Application Insights connection string

## Contributing

1. Follow the established code style and conventions
2. Run linters before committing code
3. Ensure all tests pass
4. Keep commits focused and atomic

## License

See [LICENSE](LICENSE) file for details.
