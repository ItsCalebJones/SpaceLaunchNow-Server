FROM python:3.6-slim-buster

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends git gcc python-dev  \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r /code/requirements.txt \
    && apt-get purge -y --auto-remove git gcc python-dev

COPY . /code/
WORKDIR /code/

EXPOSE 8000