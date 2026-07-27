# Vimana Framework v0.1 - Installation Guide
<img width="3840" height="2160" alt="Vimana Install-selection" src="https://github.com/user-attachments/assets/836bb079-71df-48ea-87ef-a088a19b1019" />
</br>

[![Python Version](https://img.shields.io/badge/python-3.9%2B-yellow.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-ready-green.svg)](https://github.com/features/actions)
[![GitLab/Jenkins](https://img.shields.io/badge/gitlab%2Fjenkins-ready-orange.svg)](https://gitlab.com/)
[![CircleCI](https://img.shields.io/badge/circleci-ready-brightgreen.svg)](https://circleci.com/)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.linux.org/)

## 📋 Installation Quick Navigator

Choose your preferred installation method and jump directly to the instructions:

| 🚀 **Quick & Easy** | 🔧 **Development** | 🏗️ **CI/CD Integration** |
|---|---|---|
| [**One-Line Install**](#-quick-start)<br/>*Fastest way to get started*<br/>`curl \| bash` | [**Manual Setup**](#-manual-installation)<br/>*Full control & customization*<br/>`git clone + setup` | [**⚡ GitHub Actions**](#-github-actions-integration)<br/>*Automated security scanning*<br/>`.github/workflows/` |
| [**UV Package Manager**](#option-1-uv-installation-recommended---fastest)<br/>*Modern Python tooling*<br/>`setup-uv script` | [**Docker Container**](#-docker-installation)<br/>*Isolated environment*<br/>`docker run` | [**⭕ CircleCI**](#-circleci-integration)<br/>*Enterprise CI/CD*<br/>`.circleci/config.yml` |
| [**Pip Installation**](#option-2-pip-installation-traditional)<br/>*Traditional Python setup*<br/>`setup-pip script` | [**Virtual Environment**](#option-2-pip-installation-traditional)<br/>*Python isolation*<br/>`venv + pip` | [**🦊 GitLab & 🔧 Jenkins**](#-gitlab--jenkins-integration)<br/>*Self-hosted pipelines*<br/>`.gitlab-ci.yml` |

### 🎯 **Recommended Paths:**

- **🆕 New Users**: Start with [**One-Line Install**](#-quick-start) → Get running in 30 seconds
- **👨‍💻 Developers**: Use [**Manual Setup**](#-manual-installation) → Full development environment  
- **🏢 Enterprise**: Implement [**CI/CD Integration**](#-github-actions-integration) → Automated security testing
- **🐳 DevSecOps**: Deploy with [**Docker**](#-docker-installation) → Containerized security scanning

---

## 🚀 Quick Start

### Option 1: UV Installation (Recommended - Fastest)

```bash
# Super short one-liner (installs to ~/vimana-framework)
curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
```

**Or traditional way (UV):**
```bash
# Clone the repository and set Vimana using uv
git clone -b develop https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework && source scripts/setup-uv
```
**Stage 1: Dependency Installation**
The installer downloads and configures UV, then creates a virtual environment and installs all Python dependencies. This stage handles the complete dependency resolution and builds the Vimana framework package from source.

![image](https://github.com/user-attachments/assets/73577745-d051-4fe7-a8fa-5ae0070d69fd)

**Stage 2: Plugin System Initialization**
After successful dependency installation, Vimana loads and configures its plugin ecosystem. This includes scanning for available plugins, initializing the framework core, and preparing the plugin catalog for first use.

![image](https://github.com/user-attachments/assets/9c42e79e-f2fa-4b84-9dd5-ba2ebd0415a0)

**Stage 3: Installation Complete**
The final stage shows the Vimana Framework ready for use, displaying the plugin catalog with available security testing tools. The framework is now fully operational with all plugins properly registered and accessible.

![image](https://github.com/user-attachments/assets/35614a24-2ec2-4493-97d4-6ac9c2156189)


To activate the environment and use Vimana, just run `source vfe`:
![image](https://github.com/user-attachments/assets/2fa451b4-bc8f-4d1a-abb3-374b6449c140)

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

## 🔧 Manual Installation

For developers who prefer full control over the installation process or want to customize the setup:

```bash
# Clone the repository
git clone -b develop https://github.com/s4dhulabs/vimana-framework.git
cd vimana-framework

# Create a Python virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # On Linux/macOS
# .venv\Scripts\activate   # On Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run Vimana
python vimana.py --help
```

**Manual setup benefits:**
- ✅ **Full Control**: Customize every step of the installation
- ✅ **Development Ready**: Perfect for contributing to Vimana
- ✅ **Environment Isolation**: Uses standard Python virtual environments
- ✅ **No Scripts**: Direct control without automation scripts
- ✅ **Debugging Friendly**: Easy to troubleshoot installation issues

**Usage after manual installation:**
```bash
# Activate environment (required each time)
cd ~/vimana-framework && source .venv/bin/activate

# Run Vimana commands
python vimana.py list --plugins
python vimana.py run framewalk --target-url http://example.com

# Deactivate when done
deactivate
```

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

## ⚡ GitHub Actions Integration

Vimana Framework supports running security scans directly in GitHub Actions CI/CD pipelines using various plugins.

### Quick Setup

Copy our ready-to-use template:
```bash
# Create workflow directory
mkdir -p .github/workflows

# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/github-actions-basic.yml
mv github-actions-basic.yml .github/workflows/vimana-scan.yml

# Commit and push
git add .github/workflows/vimana-scan.yml
git commit -m "Add Vimana security scanning workflow"
git push
```

### Automated Scanning in Your Repository

Or create your own workflow file:

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

For complete Django security analysis, use our comprehensive template:
```bash
# Copy Django-specific template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/github-actions-django.yml
mv github-actions-django.yml .github/workflows/vimana-django-scan.yml
```

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


## ⭕ CircleCI Integration

Vimana Framework integrates seamlessly with CircleCI for automated security testing in your CI/CD pipeline. This example demonstrates how to set up a Django application with Vimana Framewalk scanning.

### Quick Setup

Copy our ready-to-use template:
```bash
# Create config directory
mkdir -p .circleci

# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/circleci-config.yml
mv circleci-config.yml .circleci/config.yml

# Commit and push
git add .circleci/config.yml
git commit -m "Add Vimana security scanning pipeline"
git push
```

### Pipeline Overview

The CircleCI workflow consists of five sequential jobs that build, test, and security-scan a Django application:

1. **Build** - Sets up Python environment and validates Django application
2. **Test** - Runs Django unit tests to ensure application functionality
3. **Run App and Scan** - Deploys Django app and performs Vimana Framewalk security analysis
4. **Integration** - Integration testing phase
5. **Prod** - Production deployment (requires manual approval)

### CircleCI Configuration

Create a `.circleci/config.yml` file in your Django project:

```yaml
version: 2.1

jobs:
  build:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run:
          name: Install system dependencies
          command: |
            apt-get update
            apt-get install -y python3-venv curl
      - run:
          name: Set up virtual environment and install dependencies
          command: |
            python -m venv env
            source env/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            python manage.py check

  test:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run:
          name: Install dependencies and run tests
          command: |
            python -m venv env
            source env/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            python manage.py test taskManager

  run_app_and_scan:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run:
          name: Install system dependencies
          command: |
            apt-get update
            apt-get install -y python3-venv curl sudo
      - run:
          name: Set up virtual environment and run Django app
          command: |
            python -m venv env
            source env/bin/activate
            pip install --upgrade pip
            pip install -r requirements.txt
            nohup python manage.py runserver 0.0.0.0:8000 & sleep 10
          background: true
      - run:
          name: Install Vimana Framework
          command: |
            curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
      - run:
          name: Create workspace directory
          command: mkdir -p /tmp/workspace
      - run:
          name: Run Vimana Framewalk Scan
          environment:
            PYTHONWARNINGS: ignore
          command: |
            cd ~/vimana-framework && source .venv/bin/activate
            export REPORT=framewalk_report_$(date +%Y%m%d_%H%M%S).json
            vimana run framewalk --target-url http://127.0.0.1:8000/ --output $REPORT
            echo "* Final plugin report: $REPORT"
            # Copy report to workspace for artifact storage
            cp $REPORT /tmp/workspace/
      - persist_to_workspace:
          root: /tmp/workspace
          paths:
            - framewalk_report_*.json
      - store_artifacts:
          path: /tmp/workspace
          destination: vimana-reports

  integration:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run:
          command: |
            echo "~ Integration step"
            exit 1
          when: on_fail

  prod:
    docker:
      - image: python:3.10
    steps:
      - checkout
      - run: echo "~ Deploy step"

workflows:
  version: 2
  django_with_vimana:
    jobs:
      - build
      - test:
          requires:
            - build
      - run_app_and_scan:
          requires:
            - test
      - integration:
          requires:
            - test
            - run_app_and_scan
      - prod:
          type: approval
          requires:
            - integration
```

### Pipeline Execution Flow

#### 1. Pipeline Overview
The CircleCI dashboard shows the complete workflow execution with visual status indicators for each job. The pipeline runs sequentially with dependency management ensuring proper build order.
![image](https://github.com/user-attachments/assets/a7cc14ee-a283-47c9-826c-a97ecd02ed30)
![image](https://github.com/user-attachments/assets/2a3fba0f-2959-4aa3-b438-2b2879601bcc)

#### 2. Vimana Installation Process
The installation step demonstrates:
- **Automated Setup**: Vimana Framework downloads and configures automatically
- **Environment Creation**: Virtual environment setup at `/root/vimana-framework/.venv`
- **Dependency Resolution**: All required packages installed and validated
- **Symlink Creation**: Global `vimana` command made available system-wide


![image](https://github.com/user-attachments/assets/893f1b91-e96d-4803-83f5-281238a2ea7b)
![image](https://github.com/user-attachments/assets/3ed9ba95-fca6-4bf1-ac7c-32a29fabdb4a)
![image](https://github.com/user-attachments/assets/a8352b43-2cb1-42d9-8cb5-0a5f4d2a4f14)

#### 3. Security Scanning Execution
The Framewalk scan process shows:
- **Target Detection**: Django application running on `localhost:8000`
- **Framework Analysis**: Comprehensive Django security assessment
- **Report Generation**: Timestamped JSON report with findings
- **Passive Scanning**: Non-intrusive analysis maintaining application stability


![image](https://github.com/user-attachments/assets/84d15de8-3bba-4650-98fe-92c45768d94e)
![image](https://github.com/user-attachments/assets/e3d33e19-6166-4e46-a0e5-924e2def3fea)

#### 4. Artifact Management
The pipeline automatically:
- **Generates Reports**: Creates timestamped security analysis files
- **Stores Artifacts**: Preserves scan results for download and analysis
- **Workspace Persistence**: Maintains reports across pipeline stages
- **Download Access**: Provides easy access to security findings


![image](https://github.com/user-attachments/assets/0d041b39-5bcc-4994-bdc7-78238d7664b3)
![image](https://github.com/user-attachments/assets/a7cd9fe6-2ad5-44df-9c19-c9bea22773dd)

### Key Benefits

- **🔄 Automated Security**: Every code change triggers security analysis
- **📊 Comprehensive Reports**: Detailed Django framework vulnerability assessment
- **🎯 Passive Scanning**: Non-disruptive analysis during CI/CD process
- **📦 Artifact Storage**: Persistent security reports for compliance and analysis
- **🚀 Parallel Execution**: Security scanning runs alongside other pipeline jobs
- **🛡️ Framework-Specific**: Targeted Django security analysis with Framewalk plugin

### Usage Examples

```bash
# Trigger pipeline on push
git push origin main

# Download security reports
# Available in CircleCI Artifacts tab: vimana-reports/framewalk_report_*.json

# View scan results
curl -H "Circle-Token: $CIRCLECI_TOKEN" \
  "https://circleci.com/api/v1.1/project/github/$USER/$REPO/latest/artifacts"
```


## 🦊 GitLab & 🔧 Jenkins Integration

Vimana Framework can be integrated into GitLab CI/CD and Jenkins pipelines for automated security testing.

### 🦊 GitLab CI/CD Pipeline

#### Quick Setup

Copy our ready-to-use template:
```bash
# Copy basic template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/gitlab-ci-basic.yml
mv gitlab-ci-basic.yml .gitlab-ci.yml

# Or copy Django-specific template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/gitlab-ci-django.yml
mv gitlab-ci-django.yml .gitlab-ci.yml

# Commit and push
git add .gitlab-ci.yml
git commit -m "Add Vimana security scanning pipeline"
git push
```

#### Manual Configuration

Or create your own `.gitlab-ci.yml` file:

#### Basic Setup - Framework Installation Only
```yaml
stages:
  - security-test

vimana-framework-setup:
  stage: security-test
  image: python:3.10
  variables:
    PYTHONWARNINGS: ignore
  before_script:
    - apt-get update && apt-get install -y curl sudo git
    - curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
  script:
    - source vfe 
    - vimana list --plugins
```

**Pipeline execution showing successful Vimana installation:**
![image](https://github.com/user-attachments/assets/7512bef2-244e-4ef4-9379-e06f2097a727)

**Framework activation and plugin catalog display:**
![image](https://github.com/user-attachments/assets/8b7d717f-aa47-406f-b692-f2f933a5bd39)

#### Complete Pipeline - Django Application Security Analysis (Passive Framework Fingerprint)

```yaml
image: docker:20.10

services:
  - docker:dind

stages:
  - build
  - test
  - security-scan
  - integration
  - prod

variables:
  PYTHONWARNINGS: ignore

build:
  stage: build
  image: python:3.10
  before_script:
    - pip3 install --upgrade virtualenv
  script:
    - virtualenv env
    - source env/bin/activate
    - pip install -r requirements.txt
    - python manage.py check
  artifacts:
    paths:
      - env/
    expire_in: 1 hour

test:
  stage: test
  image: python:3.10
  dependencies:
    - build
  script:
    - source env/bin/activate
    - python manage.py test taskManager

vimana_framewalk_scan:
  stage: security-scan
  image: python:3.10
  variables:
    PYTHONWARNINGS: ignore
  dependencies:
    - build
  before_script:
    - apt-get update && apt-get install -y curl sudo git
    - echo "Installing Vimana Security Framework"
    - curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/scripts/install | bash
  script:
    - echo "Starting Django development server"
    - source env/bin/activate
    - nohup python manage.py runserver 0.0.0.0:8000 > django.log 2>&1 &
    - sleep 15
    - echo "Verifying Django server accessibility"
    - curl -L http://127.0.0.1:8000/taskManager/ || echo "Django server not accessible"
    - echo "Executing Vimana Framewalk security scan"
    - cd ~/vimana-framework && source .venv/bin/activate
    - export REPORT_NAME="framewalk_security_report_$(date +%Y%m%d_%H%M%S).json"
    - export REPORT_PATH="/tmp/$REPORT_NAME"
    - vimana run framewalk --target-url http://127.0.0.1:8000/ --output $REPORT_PATH
    - echo "Security analysis completed"
    - echo "Report size: $(du -h $REPORT_PATH | cut -f1)"
    - head -20 $REPORT_PATH || echo "Report file not found or empty"
  artifacts:
    name: "vimana-security-report-$CI_COMMIT_SHORT_SHA"
    paths:
      - /tmp/framewalk_security_report_*.json
    when: always
    expire_in: one week
  allow_failure: true

integration:
  stage: integration
  image: python:3.10
  script:
    - echo "Running integration tests"
    - echo "This is an integration step"
    - exit 1
  allow_failure: true

prod:
  stage: prod
  image: python:3.10
  script:
    - echo "Deploying to production"
    - echo "This is a deploy step"
  when: manual
  only:
    - main
    - master  
```

**Complete pipeline execution with all stages:**
![image](https://github.com/user-attachments/assets/ec3ea405-20c9-407b-b9ce-0d480dcdf899)

**Framewalk security scan execution and framework discovery:**
![image](https://github.com/user-attachments/assets/f5f70d0e-d1fb-49ba-8fe4-ff4888251068)

**Security analysis report generation and artifact collection:**
![image](https://github.com/user-attachments/assets/cccfe374-f794-4d31-8562-bd3849cae749)


### Key Benefits

- **🔄 Automated Security**: Security scanning integrated into GitLab CI/CD pipeline
- **📊 Detailed Reports**: Comprehensive vulnerability assessment reports
- **🎯 Flexible Integration**: Works with both basic and Django-specific pipelines
- **📦 Artifact Storage**: Security reports preserved as pipeline artifacts
- **🚀 Multi-Stage Pipeline**: Security testing alongside other CI/CD stages
- **🛡️ Customizable**: Adaptable to different project security requirements

### Usage Examples



### 🔧 Jenkins Pipeline

#### Quick Setup

Copy our ready-to-use template:
```bash
# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/Jenkinsfile

# Commit and push
git add Jenkinsfile
git commit -m "Add Vimana security scanning pipeline"
git push
```

#### Manual Configuration

Or create your own `Jenkinsfile`:

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

## 📁 Pipeline Templates

Complete pipeline templates are available in the [`docs/pipelines/`](./pipelines/) directory:

- **⚡ GitHub Actions**: `github-actions-basic.yml`, `github-actions-django.yml`
- **🦊 GitLab CI/CD**: `gitlab-ci-basic.yml`, `gitlab-ci-django.yml`
- **⭕ CircleCI**: `circleci-config.yml`
- **🔧 Jenkins**: `Jenkinsfile`

These templates provide production-ready configurations that can be customized for your specific needs.

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

- 📖 [Documentation](https://github.com/s4dhulabs/vimana-framework/docs)
- 🐛 [Report Issues](https://github.com/s4dhulabs/vimana-framework/issues)


## 🔒 Security Considerations

- Always run Vimana in isolated environments
- Use Docker containers for production deployments
- Regularly update dependencies
- Review scan results before sharing
- Follow responsible disclosure practices
- Only scan authorized targets
- Be mindful of rate limiting and legal compliance


