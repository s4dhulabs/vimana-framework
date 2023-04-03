###############################################
###############################################    
##~  Vimana Framework Docker image builder  ~## 
###############################################   
###############################################    
FROM python:3.9-slim-buster

LABEL MAINTAINER="s4dhu <s4dhul4bs[dot]protonmail[at]ch>"
MAINTAINER s4dhu <s4dhul4bs[at]protonmail[dot]ch>

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /vf0.8
COPY . /vf0.8

RUN python3.9 -m pip install --user --no-cache-dir --upgrade pip && \
    python3.9 -m pip install --user --no-cache-dir -r requirements.txt && \
    python3.9 -m pip install --user --no-cache-dir -U PyYAML

RUN groupadd -r vimana && \
    useradd -r -m -g vimana -G sudo oper && \
    chown -R oper:vimana /vf0.8/core/_dbops_/ && \
    chmod -R 750 /vf0.8/core/_dbops_/

ENV PYTHONWARNINGS=ignore
ENV PATH="/vf0.8:${PATH}"
RUN ln -s /vf0.8/vimana.py /usr/bin/vimana
CMD ["vimana", "load", "--plugins"]
ENTRYPOINT ["vimana"]


