<!-- ![Alt text](https://github.com/s4dhulabs/s4dhulabs.github.io/blob/master/resources/imgs/vimana1.png?raw=true "VIMANAFRAMEWORK") -->
![Vimana Logo](https://user-images.githubusercontent.com/89562876/229259507-fff26785-b2f7-4f0e-ad72-6c62c6b45d1d.png)
</br>
[![Python Version](https://img.shields.io/badge/python-3.9%2B-yellow.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![GitHub Actions](https://img.shields.io/badge/github%20actions-ready-green.svg)](https://github.com/features/actions)
[![GitLab/Jenkins](https://img.shields.io/badge/gitlab%2Fjenkins-ready-orange.svg)](https://gitlab.com/)
[![Platform](https://img.shields.io/badge/platform-linux-lightgrey.svg)](https://www.linux.org/)

## Overview

**Vimana** is a modular security framework for auditing and analyzing Python web applications. With a flexible plugin system, Vimana enables security professionals, developers, and researchers to assess, fuzz, and explore the security of Python-based projects using both standard and innovative techniques.

Vimana started as a web fuzzer for Python exceptions and has evolved into a comprehensive platform with plugins for:

- Persistence analysis
- Crawling and discovery
- Vulnerability tracking & CVE intelligence
- Exploitation & fuzzing
- Parsing & static analysis
- Auditing & compliance

Vimana bridges offensive and defensive security. Whether you're a developer, security engineer, or bug hunter, Vimana provides a research-driven toolkit to enhance your workflow.

---

## Getting Started

Follow the [Installation Guide](https://github.com/s4dhulabs/vimana-framework/blob/develop/docs/install.md) to set up Vimana.

- **Native install:** After setup, running `vimana` in your terminal will show:
  ![image](https://github.com/user-attachments/assets/9f643e5b-760b-4a9a-be5e-d4f9d8e5d8a6)
- **Docker:** The interface and prompt may differ, but all core features are available.

---

### First Run & Essential Commands

After installation, these commands cover most use cases:

- **`vimana list`**  
  View all available plugins, their categories, frameworks, and descriptions.
- **`vimana info <plugin>`**  
  Show detailed information about a specific plugin.
- **`vimana guide <plugin>`**  
  Display usage instructions, arguments, and practical examples for a plugin.
- **`vimana run <plugin> [options]`**  
  Execute a plugin with optional arguments.

---

#### Examples

- **List plugins:**  
  `vimana list --plugins`  
  ![image](https://github.com/user-attachments/assets/397d33ee-801d-4729-9127-315d7f650985)

- **Plugin info:**  
  `vimana info --plugin framewalk`  
  ![image](https://github.com/user-attachments/assets/6124cc1e-d674-4231-9d73-d180147fcf4d)

- **Plugin guide (arguments):**  
  `vimana guide --plugin framewalk --args`  
  ![image](https://github.com/user-attachments/assets/3542d98e-e9fa-4a46-85ca-db9bbe9371c4)

- **Plugin guide (examples):**  
  `vimana guide --plugin framewalk --examples`  
  ![image](https://github.com/user-attachments/assets/e97d52cb-31c5-4168-baf1-08e6df7f32a8)

- **Plugin guide (labs):**  
  `vimana guide --plugin framewalk --labs`  
  ![image](https://github.com/user-attachments/assets/36fc4bac-a927-4010-9424-a8a2a833a557)

> Running `vimana guide --plugin <plugin_name>` without sub-options will show the full guide (args, examples, labs).

- **Run a plugin:**  
  `vimana run framewalk --target-url http://mypyapp.com`  
  ![image](https://github.com/user-attachments/assets/e65cccff-d1bd-4255-b755-2ff6eda5029a)

---

Vimana is actively developed, with new plugins, integrations, and research features added regularly. For advanced usage and integration, see the `doc/` directory.  