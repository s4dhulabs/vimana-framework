# Vimana Framework User Guide
![image](https://github.com/user-attachments/assets/5e438547-47be-474c-8393-871fbff3c211)

## Table of Contents
- [Overview](#overview)
- [Getting Started](#getting-started)
- [Framework Navigation](#framework-navigation)
- [Essential Commands](#essential-commands)
- [Running Plugins](#running-plugins)
- [Resource Management](#resource-management)
- [Getting Help](#getting-help)
- [Examples and Best Practices](#examples-and-best-practices)
- [Advanced Features & Roadmap](#advanced-features--roadmap)

---

## Overview

The Vimana Framework provides a unified command-line interface for security testing and automation of Python web frameworks. The framework follows a plugin-based architecture where each security tool (called a "siddhi" or plugin) can be executed independently or as part of larger testing workflows.

### Execution Modes

Vimana supports three main execution approaches:

1. **CLI Mode**: Direct command-line execution of individual plugins
2. **Navigation Mode**: Interactive step-by-step configuration via `vimana start`
3. **Workflow Mode**: Execution of predefined workflows 

This guide focuses on **CLI Mode** - the most common and straightforward approach for security testing.

> **Note:** Advanced features such as **channels** (for post-exploitation, research, and automation) and **workflows** (for orchestrating complex multi-step testing) are part of Vimana's extensible architecture. These will be covered in detail in future advanced documentation.

### Core Philosophy

Vimana emphasizes:
- **Simplicity**: Clear, intuitive command syntax
- **Discoverability**: Built-in documentation and interactive menus
- **Flexibility**: Support for standalone execution, cases, and workflows
- **Extensibility**: Easy plugin development and integration

---

## Getting Started

### Command Discovery

The easiest way to understand Vimana is through its built-in command discovery system:

```bash
# See all available commands
vimana

# See what you can run
vimana run

# See what you can list
vimana list

# See what you can show
vimana show
```

Running these commands without arguments displays interactive menus that guide you through available options.

### Framework Navigation

Vimana provides intuitive navigation through its command structure:

```bash
# Main framework menu - shows all available commands
vimana

# Plugin execution menu - shows available plugins and execution options
vimana run

# Resource listing menu - shows what resources you can explore
vimana list

# Information display menu - shows what details you can view
vimana show
```

Each menu provides context-sensitive help and examples for the available options.

---

## Framework Navigation

### Main Framework Menu

Running `vimana` without arguments displays the main framework menu:

```
               about  ◉◍  Framework information and version
              create  ◉◍  Create new resources (env, vars, creds)
               flush  ◎◉  Remove recorded resources
               dbops  ◉◎  Database operations and maintenance
               guide  ◉◎  Show plugin usage examples and arguments
                help  ◎◍  Display comprehensive help for all commands
                info  ◍◍  Show detailed plugin information
                list  ◎◍  List available resources
                load  ◉◍  Load recorded sessions
                 run  ◎◉  Execute plugins, cases, or workflows
                show  ◍◎  Display detailed resource information
               start  ◍◎  Start interactive mode
```

### Plugin Execution Menu

Running `vimana run` without arguments shows execution options:

```bash
vimana run
```

This displays:
- Available plugins for execution
- Case execution options
- Workflow execution options
- Usage examples and syntax

---

## Essential Commands

### Discovering Resources

```bash
# List all available plugins
vimana list --plugins

# List plugins by framework
vimana list --plugins --framework Django

# List plugins by category
vimana list --plugins --category Audit

# List plugins by type
vimana list --plugins --type DAST

# List recorded sessions
vimana list --sessions

# List saved cases
vimana list --cases

# List exploitation channels (advanced, see roadmap)
vimana list --channels
```

### Getting Information

```bash
# Get detailed plugin information
vimana info --plugin <plugin_name>

# Show plugin documentation
vimana guide --plugin <plugin_name>

# Show plugin arguments
vimana guide --plugin <plugin_name> --args

# Show usage examples
vimana guide --plugin <plugin_name> --examples

# Show lab setup instructions
vimana guide --plugin <plugin_name> --labs
```

### Viewing Resources

```bash
# Show detailed session information
vimana show --session <session_id>

# Show case configuration
vimana show --case <case_name>

# Show channel details (advanced, see roadmap)
vimana show --channel <channel_id>

# Show channel details in compact format (advanced)
vimana show --channel <channel_id> --compact
```

### Maintenance & Database Operations

```bash
# Database operations and maintenance
vimana dbops --reset            # Reset and clean the Vimana Framework database (dangerous!)
vimana dbops --list             # List all tables and their columns/types in the database
vimana dbops --integrity-check  # Run a database integrity check (SQLite supported)
```

---

## Running Plugins

### Basic Plugin Execution

Every plugin in Vimana can be executed using the `vimana run` command:

```bash
# Basic plugin execution
vimana run <plugin_name> [options]

# Example: Running DMT against a Django application
vimana run dmt --target-url http://127.0.0.1:8000

# Example: Running JColt for FastAPI security testing
vimana run jcolt --scan-api http://api.example.com

# Example: Running PySerial for serialization vulnerability testing
vimana run pyserial --target-url http://127.0.0.1:8003
```

### Common Plugin Options

While each plugin has unique capabilities, there are standard option patterns:

#### Target Specification
```bash
--target-url        Single target URL
--target-list       Comma-separated list of targets
--file              File containing list of targets
--port              Single port number
--port-list         Comma-separated list of ports
```

#### Execution Control
```bash
--debug             Enable debug mode with detailed output
--verbose           Enable verbose mode (incremental levels)
--auto              Auto-confirm prompts and continue on errors
--threads           Number of concurrent threads (default: 3)
--timeout           HTTP request timeout in seconds (default: 5)
```

#### Output and Saving
```bash
--save-case <name>  Save current command as reusable case
--output <file>     Save results to specified file
--export-format     Output format (json, xml, html)
```

> **💡 Pro Tip**: Always use `vimana guide -p <plugin_name>` for complete and accurate documentation of any plugin's specific options and requirements.

---

## Resource Management

### Case Management

Cases allow you to save and reuse complex command configurations:

```bash
# Create and execute a case
vimana run dmt \
    --target-list 127.0.0.1,192.168.1.161 \
    --port-list 8000,8001,8002 \
    --verbose \
    --auto \
    --save-case django_audit \
    --exec-case

# Execute saved cases
vimana run --case django_audit
vimana run django_audit
vimana run !                    # Execute last case
```

### Session Management

```bash
# List recorded sessions
vimana list --sessions

# Show session details
vimana show --session <session_id>

# Load specific session
vimana load --session <session_id>
```

### Channel Management

```bash
# List exploitation channels
vimana list --channels

# List channels in summary format
vimana list --channels --summary

# Filter channels by type
vimana list --channels --channel-type RCE

# Show channel details
vimana show --channel <channel_id>

# Show channel details in compact format
vimana show --channel <channel_id> --compact
```

### Resource Cleanup

```bash
# Remove specific resources
vimana flush --session <session_id>
vimana flush --case <case_name>
vimana flush --channel <channel_id>

# Remove all resources of a type
vimana flush --sessions
vimana flush --cases
vimana flush --channels
```

---

## Getting Help

### Built-in Documentation

```bash
# Main framework help
vimana --help
vimana help

# Command-specific help
vimana run --help
vimana list --help
vimana show --help

# Plugin-specific documentation
vimana guide -p <plugin_name>

# Plugin catalog
vimana list --plugins
```

### Interactive Help

```bash
# Start interactive mode for guided configuration
vimana start

# Use command discovery menus
vimana
vimana run
vimana list
vimana show
```

### Documentation Sections

```bash
# Get complete plugin guide
vimana guide -p <plugin_name>

# Get only plugin arguments
vimana guide -p <plugin_name> --args

# Get only usage examples
vimana guide -p <plugin_name> --examples

# Get only lab setup instructions
vimana guide -p <plugin_name> --labs
```

---

## Examples and Best Practices

### Quick Start Examples

```bash
# 1. Discover what's available
vimana list --plugins

# 2. Get information about a plugin
vimana info --plugin dmt

# 3. Get plugin documentation
vimana guide -p dmt

# 4. Run the plugin
vimana run dmt --target-url http://127.0.0.1:8000

# 5. Save as a case for reuse
vimana run dmt --target-url http://127.0.0.1:8000 --save-case quick_test
```

### Framework-Specific Testing

#### Django Security Testing
```bash
# List Django-specific plugins
vimana list --plugins --framework Django

# Run comprehensive Django audit
vimana run dmt --target-url http://django-app.com:8000 --debug

# Save Django testing case
vimana run dmt \
    --target-list app1.com,app2.com \
    --port-list 8000,8001 \
    --save-case django_production_audit
```

#### FastAPI Security Testing
```bash
# List FastAPI plugins
vimana list --plugins --framework FastAPI

# Scan and test API
vimana run jcolt --scan-api http://api.example.com
vimana run jcolt --serialization-test
```

#### Python Serialization Testing
```bash
# Test serialization vulnerabilities
vimana run pyserial --target-url http://127.0.0.1:8003

# Test with saved API specification
vimana run pyserial --apispec <spec_id>
```

### Best Practices

1. **Start with Discovery**: Use `vimana list --plugins` to see what's available
2. **Read the Guide**: Always run `vimana guide -p <plugin_name>` before using a new plugin
3. **Use Cases**: Save complex configurations as cases for reproducibility
4. **Enable Debug**: Use `--debug` when learning plugin behavior
5. **Leverage Auto Mode**: Use `--auto` for unattended execution
6. **Organize Resources**: Use descriptive names for cases and maintain documentation

### Lab Environment Setup

For hands-on learning, set up test environments using vulnerable applications:

```bash
# Example: Django.nV setup for DMT testing
git clone https://github.com/nVisium/django.nV.git
cd django.nV
# Follow plugin-specific lab setup instructions from guide
```

---

## Advanced Features & Roadmap

Vimana is designed for extensibility and advanced use cases. Some features are considered advanced and will be covered in future documentation:

- **Channels**: For post-exploitation, research, and automation workflows
- **Workflows**: For orchestrating complex, multi-step, or multi-plugin testing
- **Custom Automation**: Scripting, chaining, and advanced reporting

Stay tuned for updates and advanced guides!

---

*Remember: The command discovery system is your best friend. When in doubt, run `vimana`, `vimana run`, or `vimana list` without arguments to see what's available.* 