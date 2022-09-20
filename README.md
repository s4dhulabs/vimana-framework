
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

```python
þ


       *              `'´    *
                              ˙   ٭.    ˖     
                      __'__'__         ,
             ˖          `''´   ˙              ٭   .    ˖
            -o-
             '          .*       o       .       *
        o   ˖     |
           .     -O-            `ç´    
.                 |        *     '  .     -0-
       *  o     .    '       *      .        
       ˖                ˖
       


+---------------------------------------------------------------------------------------------------------+
|                                                 siddhis                                                 |
+----------+-------------+-----------+--------------------------------------------------------------------+
| Name     | Type        | Category  | Info                                                               |
+----------+-------------+-----------+--------------------------------------------------------------------+
| djunch   | fuzzer      | framework | application fuzzer for django framework                            |
| 2pacx    | exploit     | package   | remote code execution via insecure file extraction                 |
| prana    | tracker     | framework | utility to retrieve cve ids from the official django security page |
| dmt      | tracker     | framework | tracks and exploits misconfigurations in django applications       |
| flame    | parser      | framework | traceback parser for flask applications                            |
| sttinger | fingerprint | framework | identify the framework version in a passive way                    |
| jungle   | audit       | framework | brute force utility to audit django administration portal          |
| viwec    | crawler     | discovery | simple web crawler utility                                         |
| atlatl   | persistence | framework | capture, authenticate, and persist flask debug console sessions.   |
| tictrac  | tracker     | framework | track bug tickets in django ticket system                          |
+----------+-------------+-----------+--------------------------------------------------------------------+

```

## Getting information about a module
Done that, you can get information about what a vimana module is about by running ```vimana info```, for example, with 2pacx module, an exploit one you'll do 

```
$ vimana info --module 2pacx


               Name 2pacx
             Author s4dhu <s4dhul4bs[at]prontonmail[dot]ch
               Info Remote code execution via insecure file extraction
           Category package
          Framework generic
            Package zipfile
               Type exploit
               Tags Path Traversal,Zipfile
                CWE 22,73

		The vulnerability occurs when a zipped file is sent to a
		Python application that uses the zipfile.ZipInfo() method
		from the zipfile[1] library to obtain the information
		necessary to perform the server side extraction.
		
		In this scenario, an attacker can manipulate a
		specially created .zip file, in which the filename
		(fileinfo.filename) is configured, via path traversal
		(eg: '../config/__init__.py'), by setting an arbitrary
		location for record the contents of the malicious zip
		file[2][3].
		
		The goal of the exploit is to subscribe to the content
		of some __init__.py file (zipfile.ZipInfo.writestr())
		within any directory of the exploited application.
		
		Note that there are numerous particularities necessary
		for this flaw to be exploited, one of which is the fact
		that the payload sent will only be executed immediately
		in cases where the Python application (Flask/Django)
		is running with DEBUG true, otherwise the payload will
		only be triggered when the server restarts.
		
		Another important point is that it is necessary that
		the directory specified in the filename of the sent zip
		exists on the server with an __init__.py file.
		
         References
		https://docs.python.org/2/library/zipfile.html#zipfile.ZipInfo
		https://ajinabraham.com/blog/exploiting-insecure-file-extraction-in-python-for-code-execution
		https://github.com/MobSF/Mobile-Security-Framework-MobSF/issues/358

```


## Vimana Guides
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

This command is responsible for guiding you through usage, options, and tips to get started. 

### Module required arguments

```bash
$ vimana guide --module dmt --args

		ø----------------------------------------------------------------------ø
		│└┐└│└┘┌┐│└└┘┌┐┘└┘└┐└┘│└┐┘││└┘│-  DMT ARGS  ┐│││││├┤┘│││┤└┘││└┐└┘│┌┌┐└│┐
		ø-----------+----------------------------------------------------------ø
		│ target    └┐                                                         │
		+------------+---------------------------------------------------------+
		 --target            Run DMT against a single target
		 --target-list       Run DMT against a target list (comma separated)
		 --file              Run DMT loading scope from a file
		+-----------+----------------------------------------------------------+
		│ port      └┐                                                         │     
		+------------+---------------------------------------------------------+
		 --port              Setting a single port for the target
		 --port-list         Setting a port-list (comma separated)
		 --port-range        Setting a range of ports for each target
		 --ignore-state      Ignore port status checks   
		+-----------+----------------------------------------------------------+
		│ autoload  └┐                                                         │     
		+------------+---------------------------------------------------------+
		 --nmap-xml          Load the scope from nmap xml file
		 --docker-scope      Load the scope from Docker environment
		+-----------+----------------------------------------------------------+
		│ modes     └┐                                                         │
		+------------+---------------------------------------------------------+
		 --extended-scope    Run DMT in sample mode with extended scope
		 --exit-on-trigger   Run in default mode exiting on first exception
		 --sample            Run DMT in silent sample mode 
		+-----------+----------------------------------------------------------+
		│ options   └┐                                                         │      
		+------------+---------------------------------------------------------+
		 --save-session      Save analysis results as a interactive session
		 --verbose           Enable verbosity (not enabled in sample mode)
		 --debug             Enable debug messages (not enabled in sample mode)
		 --auto              Enable auto-confirmation (default on sample mode)
		
		 * You can also see some examples with `vimana guide -m DMT -e`              

```

### Module usage examples
```bash
$ vimana guide -m dmt --examples

		ø----------------------------------------------------------------------ø
		⠞⠓⠊⠎:⠞⠓⠎⠞⠎-⠞⠊⠞⠓~⠊⠎⠞⠓⠊⠎└┐  DMT GUIDE  ⠞⠓⠊⠎.~⠞⠎⠞⠓⠊⠓⠊::::::⠞⠓⠊-⠞⠓⠊⠎
		ø---------------------└┘-----------------------------------------------ø
		
		 Run DMT in (default) analytical mode (all occurrences)
		 against a specific target and port, enabling debug mode:
		
		 $ vimana run -m dmt -t djapp1.vmnf.com -p 8000 --debug
		
		ø----------------------------------------------------------------------ø
		
		 Run DMT against a list of targets on a specific port
		 with sample mode enabled. This mode will suppress all
		 debug or verbose messages focused on triggering just one
		 exception. It aims to be fast once we're looking for
		 a single sample instead of analytical mode (default),
		 which looks for all unique occurrences:
		
		 $ vimana run \
		    --module dmt \
		    --target-list 127.0.0.1, 192.168.1.161 \
		    --port 9001 \
		    --sample
		
		ø----------------------------------------------------------------------ø
		
		 Creating a case setting DMT against a list of targets and
		 ports enabling auto-confirmation, verbose and running the
		 case with name 'djapps':
		
		 $ vimana run \
		    --module dmt \
		    --target-list 127.0.0.1, 192.168.1.161, djapp1.vmnf.com\
		    --port-list 8888,9001,8000,5001 \
		    --verbose \
		    --auto \
		    --save-case djapps \
		    --exec-case
		
		ø----------------------------------------------------------------------ø

```

### Module lab tips
```bash
$ vimana guide -m dmt --labs

		ø----------------------------------------------------------------------ø
		│└┘⠞⠓┌┐│└⠞⠓└┘┌⠞⠓┐┌┘.┌⠞⠓┬┐.└┐┘│ LAB SETUP  ┘└┐│.└┘.┌┐│⠞⠓│┬.│⠞└┘┌┬┐└┐┌.│
		ø----------------------------------------------------------------------ø
		
		 Even though there are many ways to test DMT, I encourage
		 you to set up a test environment using some Django
		 open-source projects available on GitHub. Also, you can
		 easily find many interesting images on Docker Hub to run
		 DMT against it. Check it out: https://hub.docker.com
		
		 If you're running DMT for the first time, I recommend 
		 using this purposefully vulnerable Django application 
		 provided by nVisium: 
		
		 https://github.com/nVisium/django.nV
		
		 You can simply follow the steps bellow to setup a test env
		 using django.nV:
		
		 $ git clone https://github.com/nVisium/django.nV.git
		 $ export PYTHONPATH="/usr/local/lib/python3.4/site-packages"
		 $ virtualenv -p python3 ~/django.nV_venv
		 $ source ~/django.nV_venv/bin/activate
		 $ cd django.nV
		 $ pip install -r requirements.txt
		 $ ./reset_db.sh
		 $ ./runapp.sh
		
		 In another terminal start DMT with debug and save-session
		 enabled:
		
		 $ vimana run \
		    --module dmt \
		    --target localhost \
		    --port 8000 \
		    --debug \
		    --save-session 
		
		 In case you have not set Vimana using set_env script:
		
		 $ python3 vimana.py run \
		    --module dmt \
		    --target localhost \
		    --port 8000 \
		    --debug 
		
		 * args: `vimana guide -m dmt -a`              

```


## Under active development:

|**Resource**| **Type** |      **Category**   | **Focus** |    **Status**
|  :-----:   | :-----:  |        :-----:      |   :-----: |      :-----:
|   caiman   | Plugin   | Exploitation/Scanner|    SSTI   |   :mage_man: In progress...
|   vfte    | Templates|Template engine   |    Python CVEs   |   :spider_web: Designing...
|   d4m8    | Plugin| Fuzzer   |    PyApps Forms   |   :mage_man: In progress...
|   engine    | Framework| Plugins   |    Refactory   |   :mage_man: In progress...
|   guides    | Framework| Plugins   |   Docs   |   👾: Done!
