# Vimana Framework
![Alt text](imgs/vimana1.png?raw=true "VIMANAFRAMEWORK")


Vimana is a modular framework designed to audit Python web applications. The base of the Vimana is composed of crawlers focused on frameworks (in addition to the generic ones for web), misconfiguration trackers, discovery, fuzzer and parser modules. The main idea, from where the framework emerged, is to identify, through a blackbox approach, configuration flaws and inadequate and / or insufficient implementations that allow unhandled exceptions to be triggered. Depending on the framework settings (or specific libs even when not using frameworks, for example raw wsgi) this can lead to leakage of sensitive and critical information that can allow to compromising the entire application, server, apis, databases, services and any third part software with tokens, secrets or api keys in current exposed environment variables.

Another important step performed by Vimana is to obtain and reconstruct the source code snippets of the affected modules (leaked by exceptions) that allow the discovery of hardcoded credentials, connection strings to databases, vulnerable libraries, in addition to allowing the analysis of logic of the application of a mixed perspective between the black and whitebox approaches, since the initial analysis starts from a blind test, but ends up allowing access to code snippets.
