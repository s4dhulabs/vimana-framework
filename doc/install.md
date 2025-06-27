# Vimana Framework v0.1 - Installation Guide

![image](https://github.com/user-attachments/assets/7b84db0a-0cc2-4a17-a10b-fac8b93d3927)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-yellow.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-ready-green.svg)](https://github.com/features/actions)

## 🚀 Quick Start

### Option 1: UV Installation (Recommended - Fastest)

```bash
# Clone the repository
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework

# Setup with uv (automatically installs uv if not present)
source scripts/setup-uv
```

**Why UV?**
- 10-100x faster than pip
- Automatic dependency resolution
- Built-in virtual environment management
- Lock file support for reproducible builds
- Uses `uv sync` for optimal project setup

### Option 2: One-liner Installation (Quick testing)

```bash
curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/main/scripts/abduct | bash
```

### Option 3: Manual Setup with Python Virtual Environment

```bash
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework
source scripts/setup
```

## 🐳 Docker Installation

### Option 1: Docker Compose (Recommended for development)

```bash
# Clone the repository
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework

# Start with docker-compose
docker-compose up -d

# Or run interactively
docker-compose run --rm vimana

# Stop the services
docker-compose down
```

**Benefits of Docker Compose:**
- Persistent volume mounting for data
- Easy environment management
- Port exposure for web interfaces
- Automatic restart policies

### Option 2: Direct Docker Build

```bash
# Clone the repository
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework

# Build and run using the build script
sudo sh scripts/build

# Or build manually
docker build -t vimana_framework:v0.1 .

# Run the container
docker run -it vimana_framework:v0.1
```

## 🔄 GitHub Actions Integration

Vimana Framework supports running security scans directly in GitHub Actions CI/CD pipelines using various plugins.

### Option 1: Manual Trigger

1. Go to your repository's Actions tab
2. Select "Vimana Framework Security Testing" workflow
3. Click "Run workflow"
4. Configure parameters:
   - **Target URL**: Your target (e.g., `http://localhost:8000`)
   - **Plugin**: Select the plugin you want to use
   - **Scan Mode**: Choose from available modes
5. Click "Run workflow"

### Option 2: Automated Scanning in Your Repository

Add this to your repository to run Vimana on every push:

```yaml
name: Vimana Security Scan
on: [push, pull_request]

jobs:
  vimana-scan:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - uses: astral-sh/setup-uv@v1
      with:
        version: "latest"
    - run: |
        uv sync
        sudo ln -sf $PWD/vimana.py /usr/bin/vimana
        vimana load --plugins
        vimana list --plugins 
```

### Option 3: Custom Workflow with Multiple Plugins

```yaml
name: Comprehensive Security Testing
on:
  workflow_dispatch:
    inputs:
      target_url:
        description: 'Target URL'
        required: true
        default: 'http://localhost:8000'

jobs:
  security-testing:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - uses: astral-sh/setup-uv@v1
    - run: |
        uv sync
        sudo ln -sf $PWD/vimana.py /usr/bin/vimana
        
        # Load plugins
        vimana load --plugins

        # List plugins
        vimana list --plugins
        
        # Run D4M8 form fuzzing (Django Web Forms)
        vimana run d4m8 --target-url ${{ github.event.inputs.target_url }}
        
        # Run ViewScan for code analysis (Django Views)
        vimana run viewscan --project-dir "${GITHUB_WORKSPACE}"
        
        # Add more plugins as needed
        # vimana run --plugin other_plugin --options
```

## 🚀 GitLab/Jenkins Integration

Vimana Framework can be integrated into GitLab CI/CD and Jenkins pipelines for automated security testing.

### GitLab CI/CD Pipeline

Create a `.gitlab-ci.yml` file in your repository:

```yaml
stages:
  - security-test

vimana-security-scan:
  stage: security-test
  image: python:3.9-slim
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - source ~/.bashrc
    - uv sync
    - sudo ln -sf $PWD/vimana.py /usr/bin/vimana
  script:
    - vimana load --plugins
    - vimana list --plugins
    - vimana run d4m8 --target-url $TARGET_URL
    - vimana run viewscan --project-dir "${CI_PROJECT_DIR}"
  variables:
    TARGET_URL: "http://localhost:8000"
  artifacts:
    paths:
      - core/_dbops_/
      - "*.log"
      - "*.json"
      - "*.xml"
    expire_in: 1 week
```

### Jenkins Pipeline

Create a `Jenkinsfile` in your repository:

```groovy
pipeline {
    agent any
    
    environment {
        TARGET_URL = 'http://localhost:8000'
    }
    
    stages {
        stage('Setup Vimana') {
            steps {
                sh '''
                    curl -LsSf https://astral.sh/uv/install.sh | sh
                    source ~/.bashrc
                    uv sync
                    sudo ln -sf $PWD/vimana.py /usr/bin/vimana
                '''
            }
        }
        
        stage('Load Plugins') {
            steps {
                sh '''
                    vimana load --plugins
                    vimana list --plugins
                '''
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    # Run D4M8 form fuzzing (Django Web Forms)
                    vimana run d4m8 --target-url $TARGET_URL
                    
                    # Run ViewScan for code analysis (Django Views)
                    vimana run viewscan --project-dir "${WORKSPACE}"
                '''
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'core/_dbops_/,*.log,*.json,*.xml', fingerprint: true
        }
    }
}
```

### Plugin Architecture

Vimana is a modular framework that works with plugins. Each plugin has specific capabilities:

- **D4M8**: Django Web Form Fuzzer for mapping exceptions
- **ViewScan**: Code analysis and vulnerability scanning
- **Other plugins**: Various security testing capabilities

All plugins follow the syntax: `vimana run <plugin_name> <plugin_options>`

## 📋 System Requirements

- **Python**: 3.9 or higher
- **OS**: Linux, macOS, Windows (WSL recommended)
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Storage**: 500MB free space
- **Network**: Internet connection for initial setup

## 🔧 Advanced Configuration

### Environment Variables

```bash
export VIMANA_CONFIG_PATH=/path/to/config
export VIMANA_LOG_LEVEL=DEBUG
export VIMANA_OUTPUT_FORMAT=json
```

### Custom Docker Configuration

```bash
# Build with custom tag
docker build -t my-vimana:v1.0 .

# Run with custom volumes
docker run -it -v $(pwd)/data:/vf0.1/data my-vimana:v1.0

# Run with custom environment
docker run -it -e VIMANA_LOG_LEVEL=DEBUG vimana_framework:v0.1
```

## 🛠️ Troubleshooting

### Common Issues

**Docker Permission Denied:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

**Python Virtual Environment Issues:**
```bash
# Remove existing environment
rm -rf ~/vfe0.1
# Recreate with setup script
source scripts/setup
```

**UV Installation Issues:**
```bash
# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

**GitHub Actions Issues:**
```bash
# Check workflow logs for specific errors
# Ensure target URL is accessible from GitHub Actions
# Verify plugin dependencies are installed
```

### Getting Help

- 📖 [Documentation](https://github.com/s4dhulabs/vimana-framework)
- 🐛 [Report Issues](https://github.com/s4dhulabs/vimana-framework/issues)
- 💬 [Discussions](https://github.com/s4dhulabs/vimana-framework/discussions)

## 🔒 Security Considerations

- Always run Vimana in isolated environments
- Use Docker containers for production deployments
- Regularly update dependencies
- Review scan results before sharing
- Follow responsible disclosure practices
- Only scan authorized targets
- Be mindful of rate limiting and legal compliance

---

**Note**: UV is the recommended installation method for the fastest development experience, while Docker is preferred for production deployments. GitHub Actions integration enables automated security testing in CI/CD pipelines.
