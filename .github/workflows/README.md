# Vimana Framework GitHub Actions

This directory contains GitHub Actions workflows for running Vimana Framework plugins in CI/CD environments.

## Available Workflows

### `vimana.yml` - Main Security Testing Pipeline

This workflow provides automated security testing using Vimana Framework plugins, with a focus on the D4M8 Django Web Form Fuzzer.

#### Features:
- **Plugin-Based Architecture**: Uses Vimana's modular plugin system
- **D4M8 Integration**: Django Web Form Fuzzer for exception mapping
- **Multiple Scan Modes**: Blackbox, aggressive, rule-based, and custom data scanning
- **UV Package Management**: Fast dependency installation using UV
- **Docker Integration**: Builds and tests Vimana Docker images
- **Artifact Storage**: Saves scan results as downloadable artifacts

#### Manual Trigger Parameters:
- `target_url`: The target URL to scan (e.g., http://localhost:8000)
- `plugin`: Plugin to use (d4m8, viewscan, other_plugins_coming_soon)
- `scan_mode`: Scan mode for the selected plugin (blackbox, aggressive, rule_based, custom_data)

#### D4M8 Plugin Examples:

**Blackbox Mode:**
```yaml
# Discovers and fuzzes available endpoints
python vimana.py run --plugin d4m8 --target-url http://localhost:8000
```

**Aggressive Mode with Custom Data:**
```yaml
# Comprehensive fuzzing with extended scope
python vimana.py run \
  --plugin d4m8 \
  --target-url http://localhost:8000 \
  --agressive \
  --xscope \
  --data '{"email":"test@github-actions.com","username": "github_user"}'
```

**Rule-Based Scanning:**
```yaml
# Uses predefined fuzzing rules
python vimana.py run --plugin d4m8 --scan-rules
```

**Custom Data Fields:**
```yaml
# Targeted fuzzing with specific form fields
python vimana.py run \
  --plugin d4m8 \
  --target-url http://localhost:8000 \
  --data '{"email":"admin@target.com","password":"testpass123","username":"admin_user"}'
```

#### Usage Examples:

**Manual Execution:**
1. Go to Actions tab in your repository
2. Select "Vimana Framework Security Testing"
3. Click "Run workflow"
4. Enter your target URL
5. Select plugin (d4m8 recommended)
6. Choose scan mode
7. Click "Run workflow"

**Automated Scanning:**
The workflow automatically runs on:
- Push to main/develop branches
- Pull requests to main branch

#### Available Plugins:
- **D4M8**: Django Web Form Fuzzer for mapping exceptions
- **ViewScan**: Code analysis and vulnerability scanning
- **Other plugins**: Various security testing capabilities (coming soon)

#### Output:
- Scan results stored in `core/_dbops_/`
- Log files and reports
- Docker image with plugin testing
- SARIF format vulnerability reports (if available)

## Plugin Architecture

Vimana Framework uses a modular plugin architecture:

```bash
vimana run <plugin_name> <plugin_options>
```

Each plugin has specific capabilities and options. The workflow demonstrates how to integrate different plugins into CI/CD pipelines.

## Security Considerations

- Always review scan results before sharing
- Use appropriate targets (own systems or authorized targets)
- Follow responsible disclosure practices
- Consider rate limiting for external targets
- Ensure legal compliance for security testing

## Customization

You can customize the workflow by:
- Adding new plugins to the workflow
- Modifying scan parameters and modes
- Changing trigger conditions
- Adjusting resource allocation
- Adding custom rule files for plugins

## Troubleshooting

Common issues:
- **Permission errors**: Ensure workflow has necessary permissions
- **Timeout issues**: Increase timeout for large scans
- **Plugin dependency issues**: Check plugin requirements
- **Target accessibility**: Ensure target URL is accessible from GitHub Actions
- **UV installation**: Verify UV is properly installed and configured

## Future Enhancements

- Additional plugin integrations
- Custom rule file support
- Advanced reporting features
- Multi-target scanning capabilities
- Integration with security tools (Trivy, etc.) 