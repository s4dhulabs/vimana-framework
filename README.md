# Vimana Framework
Vimana is a modular security framework designed to audit Python web applications.

![Alt text](https://github.com/s4dhulabs/s4dhulabs.github.io/blob/master/resources/imgs/vimana1.png?raw=true "VIMANAFRAMEWORK")

<!-- 
## Content

* [ Framework Structure](https://github.com/s4dhulabs/vimana-framework/wiki/Framework-Structure)
* [ Getting Started with Vimana](https://github.com/s4dhulabs/vimana-framework/wiki/Getting-Started-with-Vimana)
* [ About this Version](https://github.com/s4dhulabs/vimana-framework/wiki/About-this-version)
* [ Vimana is not](https://github.com/s4dhulabs/vimana-framework/wiki/Vimana-is-not)
* [ Use Cases](https://github.com/s4dhulabs/vimana-framework/wiki/Use-cases)
* [ Acknowledgment](https://github.com/s4dhulabs/vimana-framework/wiki/Acknowledgment)
* [ Disclaimer](https://github.com/s4dhulabs/vimana-framework/wiki/Disclaimer)
* [ Site](http://s4dhulabs.github.io/) 👾

-->

## Getting Started
The most straightforward approach to get started with Vimana Framework is by running the setup scripts like this on your Linux terminal:
```bash

$ curl -s https://raw.githubusercontent.com/s4dhulabs/vimana-framework/main/scripts/get_vimana | bash

```
You can also set it up like this:
```bash

$ git clone https://github.com/s4dhulabs/vimana-framework.git && cd vimana-framework
$ source scripts/set_env

```
After finishing the setup successfully, your terminal should look like this: 

![image](https://user-images.githubusercontent.com/89562876/190939171-5e223809-5426-455b-851f-72c072739af7.png)

With that, you have the framework itself ready. The last step is to load Vimana plugins, you can do this running: 
```bash

$ vimana load --plugins

```
## Under active development:

|**Resource**| **Type** |      **Category**   | **Focus** |    **Status**
|  :-----:   | :-----:  |        :-----:      |   :-----: |      :-----:
|   caiman   | Plugin   | Exploitation/Scanner|    SSTI   |   :mage_man: In progress...
|   vfte    | Templates|Template engine   |    Python CVEs   |   :spider_web: Designing...
|   d4m8    | Plugin| Fuzzer   |    PyApps Forms   |   :mage_man: In progress...
|   engine    | Framework| Plugins   |    Refactory   |   :mage_man: In progress...
|   guides    | Framework| Plugins   |   Docs   |   👾: Done!
