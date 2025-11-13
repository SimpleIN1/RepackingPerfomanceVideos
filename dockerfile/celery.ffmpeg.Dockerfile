FROM ubuntu:20.04
LABEL authors="SimpleIN1 <serbinovichgs@ict.nsc.ru>"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN useradd -s /bin/bash django-user \
     && mkdir -p /usr/src/app/ \
     && chown -R django-user:django-user /usr/src/app/

RUN apt-get update  \
     && apt-get install -y ffmpeg curl wget \
     && apt-get install -y software-properties-common \
     && add-apt-repository ppa:deadsnakes/ppa  \
     && apt-get install -y python3.8 python3-venv \
     && rm -rf /var/lib/apt/lists/* \
     && ln -s /usr/bin/pip3 /usr/bin/pip  \
     && ln -s /usr/bin/python3.8 /usr/bin/python

WORKDIR /usr/src/app/

USER django-user

COPY --chown=django-user:django-user requirements.txt .

RUN /usr/bin/python3.8 -m venv venv && venv/bin/python -m pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
    venv/bin/pip install -r requirements.txt

COPY --chown=django-user:django-user RepackingProject/ RepackingProject

WORKDIR /usr/src/app/RepackingProject/
