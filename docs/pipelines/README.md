# Vimana Framework - CI/CD Pipeline Templates

This directory contains ready-to-use CI/CD pipeline templates for integrating Vimana Framework security scanning into your development workflow.

## 📁 Available Templates

### ⚡ GitHub Actions
- **`github-actions-basic.yml`** - Basic Vimana installation and setup
- **`github-actions-django.yml`** - Complete Django application security analysis with Framewalk

### 🦊 GitLab CI/CD
- **`gitlab-ci-basic.yml`** - Simple framework installation and plugin listing
- **`gitlab-ci-django.yml`** - Full Django security analysis pipeline

### ⭕ CircleCI
- **`circleci-config.yml`** - Complete Django application testing with Vimana Framewalk scanning

### 🔧 Jenkins
- **`Jenkinsfile`** - Jenkins pipeline for multi-plugin security scanning

## 🚀 Quick Setup

### ⚡ GitHub Actions
```bash
# Create workflow directory
mkdir -p .github/workflows

# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/github-actions-django.yml
mv github-actions-django.yml .github/workflows/vimana-scan.yml

# Commit and push
git add .github/workflows/vimana-scan.yml
git commit -m "Add Vimana security scanning workflow"
git push
```

### 🦊 GitLab CI/CD
```bash
# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/gitlab-ci-django.yml
mv gitlab-ci-django.yml .gitlab-ci.yml

# Commit and push
git add .gitlab-ci.yml
git commit -m "Add Vimana security scanning pipeline"
git push
```

### ⭕ CircleCI
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

### 🔧 Jenkins
```bash
# Copy template
curl -O https://raw.githubusercontent.com/s4dhulabs/vimana-framework/develop/docs/pipelines/Jenkinsfile

# Commit and push
git add Jenkinsfile
git commit -m "Add Vimana security scanning pipeline"
git push
```

## 🔧 Customization

Each template can be customized for your specific needs:

- **Target URLs**: Update the application URLs being scanned
- **Plugins**: Add or remove Vimana plugins based on your framework
- **Triggers**: Modify when the pipeline runs (push, PR, schedule)
- **Artifacts**: Configure report storage and retention
- **Notifications**: Add Slack, email, or other notifications

## 📚 Documentation

For detailed setup instructions and examples, see the main [Installation Guide](../install.md).

## 🛠️ Support

- 📖 [Documentation](https://github.com/s4dhulabs/vimana-framework/docs)
- 🐛 [Report Issues](https://github.com/s4dhulabs/vimana-framework/issues) 