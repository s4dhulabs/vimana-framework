# Vimana Framework
Vimana is a modular security framework designed to audit Python applications.
![Alt text](imgs/vimana1.png?raw=true "VIMANAFRAMEWORK")

## Content
1. [ Framework Structure. ](#struct)
2. [ Starting with Vimana. ](#starting)
3. [ About this Version. ](#about)
3. [ Curiosities. ](#curio)


<a name="struct"></a>
### Framework Structure

The base of the Vimana is composed of crawlers focused on frameworks (in addition to the generic ones for web), trackers, discovery, fuzzer, parser among other types of modules. The main idea, from where the framework emerged, is to identify, through a blackbox approach, configuration flaws and inadequate and/or insufficient implementations that allow unhandled exceptions to be triggered. Depending on the framework settings (or specific libs even when not using frameworks, for example raw wsgi) this can lead to leakage of sensitive and critical information that can allow to compromising the entire application, server, apis, databases, services and any third part software with tokens, secrets or api keys in current exposed environment variables.

Another important step performed by Vimana is to obtain and reconstruct the source code snippets of the affected modules (leaked by exceptions) that allow the discovery of hardcoded credentials, connection strings to databases, vulnerable libraries, in addition to allowing the analysis of logic of the application of a mixed perspective between the black and whitebox approaches, since the initial analysis starts from a blind test, but ends up allowing access to code snippets.


<a name="starting"></a>
### Starting with Vimana

The easiest and recommended way is through Docker image build script:
```
sudo git clone https://github.com/s4dhul4bs/vimana-framework.git
cd vimana-framework && sudo ./vmnf_build
```
Or if you prefer you can follow the same steps as the script manually to build the image:
```
timedatectl set-ntp yes
sudo git clone https://github.com/s4dhul4bs/vimana-framework.git
cd vimana-framework
sudo docker build --no-cache=true --network=host -t vimana_framework:alpha .
```
Once the image has been successfully created, you can start Vimana as follows:

```sudo docker run -it --name vimana vimana_framework:alpha```

And the framework's initial menu will be displayed:

Example:

```sudo docker run -it vimana_framework:alpha run --module dmt --target-list 192.168.1.101,192.168.1.212,mypythonapp.com --port-list 5000,5001,8000 --verbose --debug --random```

This command will run the dmt module (Django Misconfiguration Tracker) against targets 192.168.1.101,192.168.1.212 and mypythonapp.com on ports 5000,5001,8000 with debug, verbose and randomization flag enabled.


<a name="about"></a>
### About this Version

This is a version with exhaustively tested features, however, with a limited number of features, so it is considered alpha. For example the fact that in this version there are only features focused on the Django framework and that work in the vast majority in homologation and/or production scenarios with DEBUG true.

**For the next version**

Features for fault tracking and fingerprinting of template engines (Genshi, Jinja, Mako, etc.) that will serve as input for other resources for automated tests of SSTI (Server Side Template Injection).

Modules focused on other development frameworks such as Flask, Web2py, Bottle and so on).


<a name="curio"></a>
### Curiosities

**The genesis of the tool**

The idea for the tool came up in 2010 during an intrusion test where (in those typical scenarios without many relevant vulnerabilities) I found numerous IPs on the internal network, with some python applications also exposed to the internet running with Django framework, WSGI and Flask, some with DEBUG true, well, it was a scenario with a lot of relevant information that could enable me to compromise the company's internal communication channels, services and developer accounts. However, I was unable, within the stipulated period, to analyze, collect and test everything that was leaked, so (in the height of despair) I imagined a ship abducting all that and putting together a report to save the project, but I didn't have one dedicated to such a purpose, so I decided to start a new one in the way I imagined.

**About the name**

According to Sanskrit texts the ancients had several types of airships called vimanas. These vehicles were used to fly through the air from city to city; to conduct aerial surveys of uncharted lands; and as delivery vehicles for awesome weapons.
