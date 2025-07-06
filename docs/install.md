# Vimana Framework v0.1 - Installation Guide

![image](https://github.com/user-attachments/assets/7b84db0a-0cc2-4a17-a10b-fac8b93d3927)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-yellow.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-ready-green.svg)](https://github.com/features/actions)
[![GitLab/Jenkins](https://img.shields.io/badge/gitlab%2Fjenkins-ready-orange.svg)](https://gitlab.com/)

## 🚀 Quick Start

### Option 1: UV Installation (Recommended - Fastest)

```bash
# Super short one-liner (installs to ~/vimana-framework)
curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
```

**Or traditional way:**
```bash
# Clone the repository and set Vimana using uv
git clone -b develop https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework && source scripts/setup-uv
```

<a href="https://asciinema.org/a/J7S2zdrmPqv6qkMfo2nW0jVAZ" target="_blank"><img src="https://asciinema.org/a/J7S2zdrmPqv6qkMfo2nW0jVAZ.svg" /></a>


**Why UV?**
- 10-100x faster than pip
- Automatic dependency resolution
- Built-in virtual environment management
- Lock file support for reproducible builds
- Uses `uv sync` for optimal project setup
- **Clean setup experience** - warnings are suppressed during installation

**Important:** Always use `source scripts/setup-uv` (not `./scripts/setup-uv`) to ensure the virtual environment stays active in your current shell session.

## 🔄 Using Vimana After Installation

If you used the one-liner installer, Vimana is installed to `~/vimana-framework`. To use it in future sessions:

```bash
# Super quick activation:
source vfe          # Activate environment from anywhere
vimana              # Run Vimana (after activation)
```

**What is `vfe`?**
- **VFE**: **V**imana **F**ramework **E**nvironment
- **`source vfe`**: Activates environment from anywhere, stays active
- Works from any directory
- Automatically checks if Vimana is properly installed
- Use `deactivate` to exit the environment

### Option 2: Pip Installation (Traditional)

```bash
# Clone to home directory and set Vimana using pip
cd ~ && git clone -b develop https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework && source scripts/setup-pip
```

**Traditional Python setup:**
- Uses standard `python -m venv` and `pip`
- Compatible with all Python environments
- Familiar workflow for Python developers
- Same clean setup experience as UV

## 🐳 Docker Installation

### Option 1: Docker Compose (Recommended for development)

```bash
# Clone the repository
git clone -b develop https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework

# Start with docker compose
docker compose up -d

# Or run interactively
docker compose run --rm vimana

# Stop the services
docker compose down
```

**Benefits of Docker Compose:**
- Persistent volume mounting for data
- Easy environment management
- Port exposure for web interfaces
- Automatic restart policies

### Option 2: Direct Docker Build

```bash
# Clone the repository
git clone -b develop https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework

# Build and run using the build script
sudo sh scripts/build

# Or build manually
docker build -t vimana_framework:v0.1 .

# Run the container
docker run -it vimana_framework:v0.1
```

## 🔄 GitHub Actions Integration

Vimana Framework supports running security scans directly in GitHub Actions CI/CD pipelines using various plugins.

### Automated Scanning in Your Repository

Add this to your repository to run Vimana on every push:

```yaml
name: Vimana Workflow

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  vimana_scan:
    runs-on: ubuntu-22.04   
    steps:
      - uses: actions/checkout@v4

      - name: Setup python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install Vimana
        run: |
          curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
          export PATH="$HOME/.local/bin:$PATH"
          source $HOME/.local/bin/env || true

```

When the workflow runs successfully, you'll see output similar to the images below, showing:

1. The successful installation and setup of Vimana Framework
2. The environment configuration and path setup
3. A list of available security scanning plugins ready to be used in your CI/CD pipeline

These screenshots demonstrate that Vimana is properly integrated into your GitHub Actions workflow and ready to perform security scans:


![image](https://github.com/user-attachments/assets/03a894c2-285d-403e-9b10-f03c5dad439c)
![image](https://github.com/user-attachments/assets/d5580dc5-6d45-414b-a426-e3162159b6b3)
![image](https://github.com/user-attachments/assets/c6d71535-76cd-4c66-8969-a27dc1348a5c)
![image](https://github.com/user-attachments/assets/7f82e021-8ab0-438d-955a-778eb9364a73)

### Running plugins (framewalk workflow)

Below is an example workflow that demonstrates how to use Vimana's framewalk plugin to scan a Django application for security vulnerabilities. The workflow will:

1. Install and configure Vimana Framework
2. Start a Django test application 
3. Run the framewalk plugin against the application
4. Generate and store the scan report artifact

Here's the complete workflow:

```yaml
name: Vimana Framewalk Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build_app:
    runs-on: ubuntu-22.04   
    steps:
      - uses: actions/checkout@v4

      - name: Setup python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install venv and distutils for Python
        run: |
          sudo apt-get update
          sudo apt-get install -y python3.10-venv python3.10-distutils

      - name: Set up venv and install dependencies
        run: |
          python3.10 -m venv env
          source env/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
          python manage.py check

  run_app_and_scan:
    runs-on: ubuntu-22.04   
    steps:
      - uses: actions/checkout@v4

      - name: Setup python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install venv and distutils for Python
        run: |
          sudo apt-get update
          sudo apt-get install -y python3.10-venv python3.10-distutils

      - name: Set up venv and run the App
        run: |
          python3.10 -m venv env
          source env/bin/activate
          pip install --upgrade pip
          pip install -r requirements.txt
          nohup python manage.py runserver 0.0.0.0:8000 & sleep 10

      - name: Install Vimana
        run: |
          curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
          export PATH="$HOME/.local/bin:$PATH"
          source $HOME/.local/bin/env || true

      - name: Run Vimana Framewalk
        env:
          PYTHONWARNINGS: ignore
        run: |
          cd ~/vimana-framework && source .venv/bin/activate
          export REPORT=framewalk_report_$(date +%Y%m%d_%H%M%S).json
          vimana run framewalk --target-url http://127.0.0.1:8000/ --output $REPORT
          echo "REPORT=$REPORT" >> $GITHUB_ENV
          echo "* Final plugin report: $REPORT"

      - name: Upload Framewalk Report
        uses: actions/upload-artifact@v4
        with:
          name: framewalk-report
          path: ~/vimana-framework/${{ env.REPORT }}

```
![image](https://github.com/user-attachments/assets/44e7dffc-a034-400c-ab73-9e9d470459a9)
![image](https://github.com/user-attachments/assets/5bd90ec8-cf36-4e98-85a7-a8053cd84907)
![image](https://github.com/user-attachments/assets/0a7d00b3-2028-4ce2-9df1-d56333229ca5)
![image](https://github.com/user-attachments/assets/4b60d400-c817-4fe8-b226-eb9fb7f93b88)


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

**Virtual Environment Not Active:**
```bash
# If you see the default prompt instead of (vimana-framework) >
# Make sure you used 'source' not './' to run the setup script
source scripts/setup-uv

# Or manually activate the environment
source .venv/bin/activate
export VIRTUAL_ENV_DISABLE_PROMPT=1
export PS1="(vimana-framework) > "
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

**Note**: *UV is the recommended installation method for the fastest development experience, while Docker is preferred for production deployments. GitHub Actions integration enables automated security testing in CI/CD pipelines.*
