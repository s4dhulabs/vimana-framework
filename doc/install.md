
# Vimana Framework v0.8 - Installation Guide

![image](https://user-images.githubusercontent.com/89562876/229259675-ff5648aa-8a06-4145-9c6a-673f643ec00b.png)

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
