FROM python:3.8.10-slim AS builder
LABEL authors="SimpleIN1 <serbinovichgs@ict.nsc.ru>"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -s /bin/bash django-user \
     && mkdir -p /usr/src/app/ \
     && chown -R django-user:django-user /usr/src/app/

WORKDIR /usr/src/app/

USER django-user

COPY --chown=django-user:django-user requirements.txt .

RUN python -m venv venv && venv/bin/python -m pip install --upgrade pip
RUN --mount=type=cache,target=/root/.cache/pip \
    venv/bin/pip install -r requirements.txt

COPY --chown=django-user:django-user RepackingProject/ RepackingProject
RUN chown -R django-user:django-user /usr/src/app/RepackingProject/

WORKDIR /usr/src/app/RepackingProject

FROM builder AS server

FROM builder AS celery


