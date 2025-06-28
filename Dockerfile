#  __ _
#   \/imana 2016
#   [|-ramewørk
#
#
# Author: s4dhu
# Email: <s4dhul4bs[dot]protonmail[at]ch>
# Git: @s4dhulabs
# Mastodon: @s4dhu
# 
# This file is part of Vimana Framework Project.

FROM python:3.11-slim

LABEL maintainer="s4dhu <s4dhul4bs[dot]protonmail[at]ch>"

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /vf0.1
COPY . /vf0.1

# Install system dependencies and build tools
RUN apt-get update && apt-get install -y \
    sudo \
    gcc \
    python3-dev \
    && python -m pip install --user --no-cache-dir --upgrade pip \
    && python -m pip install --user --no-cache-dir -r requirements.txt \
    && python -m pip install --user --no-cache-dir -U PyYAML \
    && apt-get remove -y gcc python3-dev \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create user and set permissions
RUN groupadd -r vimana && \
    useradd -r -m -g vimana -G sudo oper && \
    chown -R oper:vimana /vf0.1/core/_dbops_/ && \
    chmod -R 750 /vf0.1/core/_dbops_/

# Set environment variables
ENV PYTHONWARNINGS=ignore::SyntaxWarning,ignore::DeprecationWarning,ignore::PendingDeprecationWarning
ENV PATH="/vf0.1:${PATH}"

# Create symlink
RUN ln -s /vf0.1/vimana.py /usr/bin/vimana

# Set default command
CMD ["vimana", "load", "--plugins"]
ENTRYPOINT ["vimana"]





