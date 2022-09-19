
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

## Overview

Vimana is a modular security framework designed to audit Python web applications using different and sometimes uncommon approaches.  

In the beginning, the main goal behind this Framework was to act as a web fuzzer to identify Python exceptions. That was the core idea. Later it became just another feature that can be invoked by other siddhis or directly via command line with ```vimana run --module <module_name> ```. In the current releases, there are available module types like:

* persistence
* crawlers
* trackers
* exploits
* fuzzers
* parses
* audit


Lately, Vimana is walking to its maturity while a Framework with a robust core to support modularization, various integrations, and post-analysis features to enrich security assessments. In addition, many new siddhis (vimana plugins) are consistently being researched and developed. 

Vimana aims not to take a side as a defensive or offensive tool. Instead, the motivation here is to mix those both perspectives, allowing a software developer to audit their projects, for example, and give offensive, security engineer, and bug hunter folks a great resource to their arsenals. 

With time, this project has revealed some promising capabilities to support security research related to Python Frameworks and applications, and it has recently been one of the current studies. In other words, research about how to support research goals. Quite meta-research stuff. I have no idea where it goes, but I've some clues, and it is worth it.     


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

![image](https://user-images.githubusercontent.com/89562876/190946974-6ff0b2a7-2005-41b2-9666-bd4d85cce365.png)

With that, you have the framework itself ready. The last step is to load Vimana plugins, you can do this running: 
```bash

$ vimana load --plugins

```
![image](https://user-images.githubusercontent.com/89562876/190946770-fc6328a6-0867-4692-9344-5e653d61b8ad.png)

It will register all vimana modules. At the end of this process, the Framework will show a table with all available modules loaded. 

![image](https://user-images.githubusercontent.com/89562876/190948039-c3dbdf32-c439-4c59-b76c-ace1b200a9ea.png)

## Getting information about a module
Done that, you can get information about what a vimana module is about by running ```vimana info```, for example, with 2pacx module, an exploit one you'll do 

```
$ vimana info --module 2pacx

```

![image](https://user-images.githubusercontent.com/89562876/191022863-501f04ab-aaaf-4c57-933b-212cd5668b12.png)

### Vimana Guides
In version 0.7 was introduced a new command to guide usage, modules required arguments, usage examples, and tips to set up a lab for tests. 

You can see the help for this new command by just typing: 


```yaml
$ vimana guide

 ˙              ٭                   .    ˖
              .             :. *
                :  └┐'┌┘          . :  .
                └┐// ' \\┌┘
        ¨⣠⠛⠛⠛⠛⠛---=======---⠛⠛⠛⠛⠛⣄      .'
       .::::__\├ ┤/⠛⠛⣄⣇⣷\├ ┤/__::::.
               '-'\_____/'-' v0.7         ⣄
               :: '│.│.│' .


        [guide]

    Show usage examples

    → Usage: vimana guide --module <module name> <options>
    
    Examples:

        # Show full DMT plugin guide
        $ vimana guide --module dmt
        $ vimana guide -m dmt

        # Show DMT plugin arguments
        $ vimana guide --module DMT -args
        $ vimana guide -m dmt -a

        # Show only usage examples
        $ vimana guide --module dmt --examples
        $ vimana guide -m dmt -e

        # Show lab setup tips:
        $ vimana guide -m dmt --labs
        $ vimana guide -m dmt -l

```

## Under active development:

|**Resource**| **Type** |      **Category**   | **Focus** |    **Status**
|  :-----:   | :-----:  |        :-----:      |   :-----: |      :-----:
|   caiman   | Plugin   | Exploitation/Scanner|    SSTI   |   :mage_man: In progress...
|   vfte    | Templates|Template engine   |    Python CVEs   |   :spider_web: Designing...
|   d4m8    | Plugin| Fuzzer   |    PyApps Forms   |   :mage_man: In progress...
|   engine    | Framework| Plugins   |    Refactory   |   :mage_man: In progress...
|   guides    | Framework| Plugins   |   Docs   |   👾: Done!
