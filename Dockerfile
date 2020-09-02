###############################################    
##~  Vimana Framework Docker image builder  ~## 
###############################################    

# ~ Basic information
FROM ubuntu:18.04
LABEL MAINTAINER="s4dhu <s4dhul4bs[dot]protonmail[at]ch>"
MAINTAINER s4dhu <s4dhul4bs[at]protonmail[dot]ch>

# ~ To avoid time sync issue in apt
VOLUME	/etc/timezone:/etc/timezone:ro
VOLUME	/etc/localtime:/etc/localtime:ro

# ~ update and install required dependencies
RUN apt-get clean && \
    apt-get update && \
    apt-get install --quiet --yes --fix-missing \
    locales \
    apt-transport-https \
    apt-utils \
    git \
    python3 \ 
    python3-pip && \
    apt-get autoremove --purge -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# ~ environment settings
RUN locale-gen en_US.UTF-8
ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

# ~ vimana settings
RUN groupadd -r vimana && \
    useradd -r -m -g vimana oper
RUN usermod -aG sudo oper

USER oper
RUN mkdir ~/vmnf_alpha
WORKDIR ~/vmnf_alpha
COPY . .
RUN pip3 install -r requirements.txt

# ~ Vimana entrypoint
ENTRYPOINT ["python3","vimana.py"]
