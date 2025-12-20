# GitHub Copilot instructions

This repo contains an Azure Functions + Static Web App demo with Azure AI Foundry resources deployed via Bicep.

## Scope and safety

- Prefer changing only `infra/`, `scripts/`, and `.gitignore` for infrastructure work.
- Never commit secrets or sensitive outputs. Do not output or persist connection strings, instrumentation keys, storage keys, or deployment artifacts in tracked files.
- Keep local deployment artifacts under `infra/.local/` (ignored by git).

## Infrastructure (Bicep) conventions

- Primary template: `infra/main.bicep`.
- Use managed identities + RBAC over access keys wherever feasible.
- When using Key Vault references in Function App app settings **and** a user-assigned identity, set:
  - `properties.keyVaultReferenceIdentity` to the user-assigned identity resource ID.
- Ensure Azure AI Foundry resources use explicit `publicNetworkAccess: 'Enabled'` unless the template also provisions appropriate private networking.

## Deployment conventions

- Use `infra/deploy.sh` for repeatable provisioning.
- The script should write any outputs/results to `infra/.local/` only.
- Bicep validation should use `az bicep build --file infra/main.bicep`.

## Environment generation

- Prefer `scripts/generate-env.sh` to derive values from Azure resource properties rather than deployment outputs.
