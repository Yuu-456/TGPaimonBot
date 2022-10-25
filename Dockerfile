FROM debian:11
FROM python:3.10.6-buster
FROM nikolaik/python-nodejs:python3.9-nodejs18

WORKDIR  /alembic/
WORKDIR  /core/
WORKDIR  /metadata/
WORKDIR  /plugins/
WORKDIR  /modules/
WORKDIR  /resources/
WORKDIR  /test/
WORKDIR  /utils/

RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip3 install --upgrade pip setuptools
RUN apt-get -y install git
RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get install libxml2-dev libxslt-dev python
RUN pip3 install --upgrade poetry 
RUN poetry install --extras pyro
RUN ./run.py

CMD ["python3", "-m", "TGPaimonBot"]
