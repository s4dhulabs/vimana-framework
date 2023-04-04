
# Vimana Framework v0.8 - Installation Guide

![image](https://user-images.githubusercontent.com/89562876/229795288-6994f6e4-735a-4d6a-9dbb-68b9dbe24400.png)

## Using Curl

```bash

curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/main/scripts/abduct | bash

```
## Using setup script

```bash
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework
source scripts/setup
```

These two options above set a Python3.9 virtual environment to run the framework, the most recommended way to try Vimana out lately (if you're running it in your OS). 

## Using Docker

1. Build the Docker image:

```bash
docker build -t vimana https://github.com/s4dhulabs/vimana-framework.git
```

```bash
git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework
sudo sh scripts/build

```

2. Run the Docker image:

```bash
docker run -it vimana_framework:v0.8 
```

## GitActions
```bash
soon... 
```
