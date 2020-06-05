# Vimana Framework
![Alt text](imgs/vimana1.png?raw=true "VIMANAFRAMEWORK")


Vimana is a modular framework designed to audit Python web applications. The base of the Vimana is composed of crawlers focused on frameworks (in addition to the generic ones for web), misconfiguration trackers, discovery, fuzzer, parser and SAST modules. The main idea, from where the framework emerged, is to identify, through a blackbox approach, configuration flaws and inadequate and / or insufficient implementations that allow unhandled exceptions to be triggered. Depending on the framework settings (or specific libs even when not using frameworks, for example raw wsgi) this can lead to leakage of sensitive and critical information that can allow to compromising the entire application, server, apis, databases, services and any third part software with tokens, secrets or api keys in current exposed environment variables.

Another important step performed by Vimana is to obtain and reconstruct the source code snippets of the affected modules (leaked by exceptions) that allow the discovery of hardcoded credentials, connection strings to databases, vulnerable libraries, in addition to allowing the analysis of logic of the application of a mixed perspective between the black and whitebox approaches, since the initial analysis starts from a blind test, but ends up allowing access to code snippets.


**The genesis of the tool**

The idea for the tool came up in 2010 during an intrusion test where (in those typical scenarios without many relevant vulnerabilities) I found numerous IPs on the internal network, with some python applications also exposed to the internet running with Django framework, WSGI and Flask, some with DEBUG true, well, it was a scenario with a lot of relevant information that could enable me to compromise the company's internal communication channels, services and developer accounts. However, I was unable, within the stipulated period, to analyze, collect and test everything that was leaked, so (in the height of despair) I imagined a ship abducting all that and putting together a report to save the project, but I didn't have one dedicated to such a purpose, so I decided to create it.

**About the name**

According to Sanskrit texts the ancients had several types of airships called vimanas. These vehicles were used to fly through the air from city to city; to conduct aerial surveys of uncharted lands; and as delivery vehicles for awesome weapons.

**How to use**

The easiest and recommended way is through Docker containers:
```
sudo git clone https://github.com/s4dhul4bs/vimana-framework.git
cd vimana-framework
sudo docker build --network=host -t vimana_framework .
```
Once the image has been successfully created, you can call to start a Vimana container as follows:

```sudo docker run -it --name vimana vimana_framework:latest```

And the framework's initial menu will be displayed:


