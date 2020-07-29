# Vimana Framework
Vimana is a modular security framework designed to audit Python applications.
![Alt text](imgs/vimana1.png?raw=true "VIMANAFRAMEWORK")

## Content
1. [ Framework Structure. ](#struct)
2. [ Starting with Vimana. ](#starting)
3. [ About this Version. ](#about)
3. [ Curiosities. ](#curio)
4. [ Acknowledgment. ](#ack)



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


Explaining the command line syntax above:

```run```         Command to run a siddhi (vimana framework module) in inline mode (in this case, module DMT, Django Misconfiguration Tracker)

```--target-list``` The framework supports several types of scope definition arguments (although this also depends on the arguments expected by each module). In this case, a list of IPs and URLs was used with the argument target-list (comma-separated).

```--post-list``` Here, as with the definition of targets, the ports also accept various formats, in this case the port-list with a list of ports to be tested is being used. An important note, when you do not want the defined port to be tested before the chosen module is invoked, the `` --ignore-state`` argument must be passed so that the state of the port will not be checked.

```--verbose```   Enable verbose mode in realtime issues presentation

```--debug```     Enable Vimana debug mode,showing realtime technical information about execution 

```--random```    Enable randomize, this flag, enable randomization in supported modules (for example user-agent, cookies, tokens, etc) 


<a name="about"></a>
### About this Version

This is a version with exhaustively tested features, however, with a limited number of features, so it is considered alpha. For example the fact that in this version there are only features focused on the Django framework and that work in the vast majority in homologation and/or production scenarios with DEBUG true.

**For the next releases**

In addition to the general improvements in the entire framework structure and in the siddhis already available, there are other important points that are:

* Features for tracking and fingerprinting template engines (like Genshi, Jinja, Mako, etc.) 
* Resources for automated SSTI tests (Server Side Template Injection)
* New fuzzers rules for Django e others frameworks
* Some lib exploits
* Resources to generate custom payloads on app context
* New siddhis focused on other development frameworks such as Flask, Web2py, Bottle and so on)
* App Crawler


<a name="curio"></a>
### Curiosities

**The genesis of the tool**

The idea for the tool came up in 2010 during an intrusion test where (in those typical scenarios without many relevant vulnerabilities) I found numerous IPs on the internal network, with some python applications also exposed to the internet running with Django framework, WSGI and Flask, some with DEBUG true, well, it was a scenario with a lot of relevant information that could enable me to compromise the company's internal communication channels, services and developer accounts. However, I was unable, within the stipulated period, to analyze, collect and test everything that was leaked, so (in the height of despair) I imagined a ship abducting all that and putting together a report to save the project, but I didn't have one dedicated to such a purpose, so I decided to start a new one in the way I imagined.

**About the name**

According to Sanskrit texts the ancients had several types of airships called vimanas. These vehicles were used to fly through the air from city to city; to conduct aerial surveys of uncharted lands; and as delivery vehicles for awesome weapons.



<a name="curio"></a>
### Acknowledgment

