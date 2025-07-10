# Vimana Framework User Guide

## Table of Contents
- [Overview](#overview)
- [Basic Command Structure](#basic-command-structure)
- [Running Plugins](#running-plugins)
- [Plugin Discovery and Documentation](#plugin-discovery-and-documentation)
- [Advanced Usage Patterns](#advanced-usage-patterns)
- [Case Management](#case-management)
- [Examples and Best Practices](#examples-and-best-practices)

---

## Overview

The Vimana Framework provides a unified command-line interface for security testing and automation of Python web frameworks. The framework follows a plugin-based architecture where each security tool (called a "siddhi" or plugin) can be executed independently or as part of larger testing workflows.

### Core Philosophy

Vimana emphasizes:
- **Simplicity**: Clear, intuitive command syntax
- **Discoverability**: Built-in documentation and examples for every plugin
- **Flexibility**: Support for standalone execution, cases, and workflows
- **Extensibility**: Easy plugin development and integration

---

## Basic Command Structure

The primary command pattern for Vimana follows this structure:

```bash
vimana run <plugin_name> <plugin_options>
```

### Command Variations

```bash
# Basic plugin execution
vimana run <plugin_name> [options]

# Case execution
vimana run --case <case_name>
vimana run --case @<case_id>

# Workflow execution
vimana run <workflow_name>

# Quick re-execution of last case
vimana run !
```

---

## Running Plugins

### Plugin Execution Basics

Every plugin in Vimana can be executed using the `vimana run` command. The framework includes 16 DAST (Dynamic Application Security Testing) tools, 1 SAST (Static Application Security Testing) tool, and 3 payload generators.

```bash
# Example: Running DMT against a Django application
vimana run dmt --target-url http://127.0.0.1:8000

# Example: Running JColt for FastAPI security testing
vimana run jcolt --scan-api http://api.example.com

# Example: Running PySerial for serialization vulnerability testing
vimana run pyserial --target-url http://127.0.0.1:8003
```

### Common Plugin Options

While each plugin has unique capabilities, there are standard option patterns based on plugin type. Understanding these patterns helps you quickly get started with any plugin, but **always use `vimana guide -p <plugin_name>` for complete and accurate documentation**.

#### Option Categories by Plugin Type

| **DAST Plugins** (Dynamic Testing) | **SAST Plugins** (Static Analysis) | **Universal Options** |
|-------------------------------------|-------------------------------------|----------------------|
| `--target-url` - Single target URL | `--project-dir` - Project directory path | `--verbose` - Enable detailed output |
| `--target-list` - Multiple targets (comma-separated) | `--framework` - Target framework (django, flask, fastapi) | `--debug` - Enable debug messages |
| `--port` - Target port | `--framework-version` - Specific version to analyze | `--auto` - Auto-confirm prompts |
| `--port-list` - Multiple ports | `--source-dirs` - Additional source directories | `--save-case <name>` - Save as reusable case |
| `--file` - Load targets from file | `--exclude-dirs` - Directories to exclude | `--export-format` - Output format (json, xml, html) |
| `--docker-scope` - Use Docker targets | `--include-tests` - Include test files in analysis | `--output` - Output file path |
| `--scan-mode` - Testing mode (sample, full, etc.) | `--config-file` - Analysis configuration file | `--timeout` - Operation timeout |

#### Specialized Options by Domain

| **API Testing** (JColt, PySerial) | **Web App Testing** (DMT, D4M8) | **Framework Analysis** |
|------------------------------------|----------------------------------|------------------------|
| `--scan-api` - Discover and save API spec | `--sample` - Fast single-occurrence mode | `--fingerprint` - Identify framework/version |
| `--apispec` - Use saved specification | `--exit-on-trigger` - Stop on first finding | `--enumerate-versions` - List supported versions |
| `--list-specs` - Show saved specifications | `--extended-scope` - Comprehensive analysis | `--check-dependencies` - Analyze dependencies |
| `--serialization-test` - Test serialization vulnerabilities | `--save-session` - Save interactive session | `--version-compare` - Compare against known versions |
| `--pydantic-test` - Test Pydantic models | `--disable-cache` - Skip caching mechanisms | `--security-headers` - Analyze security headers |

#### Important Notes

- **Plugin-Specific Options**: Each plugin has unique capabilities beyond these common patterns
- **Required vs Optional**: Some options are required, others are optional with sensible defaults
- **Parameter Formats**: Check the guide for specific format requirements (e.g., comma-separated lists)
- **Compatibility**: Not all options work together; the guide explains valid combinations

> **💡 Pro Tip**: The option patterns above are guidelines. For definitive information about any plugin's options, requirements, and usage examples, always run:
> ```bash
> vimana guide -p <plugin_name>
> ```

---

## Plugin Discovery and Documentation

### The Guide System

Vimana includes a comprehensive built-in documentation system accessible via the `guide` command. This is your primary resource for understanding any plugin's capabilities and usage.

### Getting Complete Plugin Documentation

```bash
# View full plugin guide (examples, arguments, lab setup)
vimana guide -p <plugin_name>
vimana guide --plugin <plugin_name>

# Example: Complete DMT documentation
vimana guide -p dmt
```

This displays:
- **Plugin Overview**: Purpose and capabilities
- **Usage Examples**: Real-world command examples with explanations
- **Arguments Reference**: Complete list of available options
- **Lab Setup**: Instructions for setting up test environments

### Getting Specific Documentation Sections

```bash
# View only plugin arguments
vimana guide -p <plugin_name> --args
vimana guide -p <plugin_name> -a

# View only usage examples
vimana guide -p <plugin_name> --examples
vimana guide -p <plugin_name> -e

# View only lab setup instructions
vimana guide -p <plugin_name> --labs
vimana guide -p <plugin_name> -l
```

### Example: DMT Plugin Documentation

```bash
# Get complete DMT guide
vimana guide -p dmt

# Get only DMT arguments
vimana guide -p dmt --args

# Get only DMT examples
vimana guide -p dmt --examples

# Get only DMT lab setup
vimana guide -p dmt --labs
```

---

## Advanced Usage Patterns

### Target Specification Methods

Vimana supports multiple ways to specify targets:

```bash
# Single target
vimana run dmt --target localhost --port 8000

# Multiple targets
vimana run dmt --target-list 127.0.0.1,192.168.1.161 --port 9001

# Target file (format: target:port per line)
vimana run dmt --file scope.txt

# Docker environment targets
vimana run dmt --docker-scope

# Nmap XML import
vimana run dmt --nmap-xml scan_results.xml
```

### Execution Modes

Different plugins support various execution modes:

```bash
# Sample mode (fast, single occurrence)
vimana run dmt --target localhost --port 8000 --sample

# Exit on first trigger
vimana run dmt --target localhost --port 8000 --exit-on-trigger

# Extended scope analysis
vimana run dmt --target localhost --port 8000 --extended-scope

# Debug mode with verbose output
vimana run dmt --target localhost --port 8000 --debug --verbose
```

### Session Management

```bash
# Save analysis results as interactive session
vimana run dmt --target localhost --port 8000 --save-session

# Enable auto-confirmation for unattended execution
vimana run dmt --target localhost --port 8000 --auto
```

---

## Case Management

Cases allow you to save and reuse complex command configurations, making it easy to repeat security assessments or share testing procedures.

### Creating Cases

```bash
# Create and execute a case
vimana run dmt \
    --target-list 127.0.0.1,192.168.1.161,djapp1.vmnf.com \
    --port-list 8888,9001,8000,5001 \
    --verbose \
    --auto \
    --save-case djapps \
    --exec-case
```

### Executing Saved Cases

```bash
# Run case by name
vimana run --case djapps

# Run case by ID
vimana run --case @cf1

# Run the most recently created case
vimana run !
```

### Case Benefits

- **Reproducibility**: Exact same testing conditions
- **Collaboration**: Share testing procedures with team members
- **Automation**: Integrate into CI/CD pipelines
- **Documentation**: Cases serve as executable documentation

---

## Examples and Best Practices

### FastAPI Security Testing with JColt

```bash
# Scan API and save specification
vimana run jcolt --scan-api http://api.example.com

# List available specifications
vimana run jcolt --list-specs

# Run serialization tests against saved spec
vimana run jcolt --serialization-test

# Run with custom payload builder
vimana run jcolt --serialization-test --set-custom-payload
```

### Python Serialization Testing with PySerial

```bash
# Test using saved API specification
vimana run pyserial --apispec aS0949

# Test with direct URL
vimana run pyserial --target-url http://127.0.0.1:8003

# Test specific serialization categories
vimana run pyserial --target-url http://127.0.0.1:8003 --test-categories depth_testing,type_confusion
```

### Django Security Testing with DMT

```bash
# Basic analytical mode (comprehensive)
vimana run dmt --target djapp1.vmnf.com --port 8000 --debug

# Fast sample mode
vimana run dmt --target-list 127.0.0.1,192.168.1.161 --port 9001 --sample

# Complex multi-target assessment
vimana run dmt \
    --target-list 127.0.0.1,192.168.1.161,djapp1.vmnf.com \
    --port-list 8888,9001,8000,5001 \
    --verbose \
    --auto \
    --save-case production_scan
```

### Plugin-Specific Options

Each plugin has unique capabilities. Always consult the plugin guide for specific options:

```bash
# Check what a plugin can do
vimana guide -p <plugin_name>

# Example: JColt-specific options
vimana run jcolt --pydantic-test --test-types validation_bypass,injection
vimana run jcolt --apispec aS0949 --list-pydantic-models
vimana run jcolt --fingerprint --target-url http://api.example.com
```

### Best Practices

1. **Start with the Guide**: Always run `vimana guide -p <plugin_name>` before using a new plugin
2. **Use Cases for Repeatability**: Save complex configurations as cases
3. **Enable Debug for Learning**: Use `--debug` when learning plugin behavior
4. **Leverage Auto Mode**: Use `--auto` for unattended execution
5. **Organize Your Tests**: Use descriptive case names and maintain documentation

### Lab Environment Setup

For hands-on learning, set up test environments using vulnerable applications:

```bash
# Example: Django.nV setup for DMT testing
git clone https://github.com/nVisium/django.nV.git
cd django.nV
# Follow plugin-specific lab setup instructions from guide
```

---

## Getting Help

### Built-in Documentation

```bash
# Main framework help
vimana --help

# Plugin-specific documentation
vimana guide -p <plugin_name>

# Plugin catalog
vimana list --plugins
```

### Community Resources

- **Installation Guide**: [docs/install.md](install.md)
- **CI/CD Integration**: [docs/pipelines/](pipelines/)
- **Plugin Development**: Coming soon
- **API Reference**: Coming soon

---

*Remember: The `guide` command is your best friend. When in doubt, run `vimana guide -p <plugin_name>` to understand any plugin's capabilities, arguments, and usage patterns.* 