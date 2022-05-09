FROM python:3.10.4-slim-buster

ARG SSH_PRIVATE_KEY
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1

COPY src/ /code/
WORKDIR /code/

RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends git ssh gcc python-dev libsqlite3-dev libpng-dev libjpeg-dev
RUN rm -rf /var/lib/apt/lists/*

ARG EXTRA_INDEX_URL
RUN pipenv install --deploy
RUN apt-get purge -y --auto-remove git gcc python-dev libsqlite3-dev libpng-dev libjpeg-dev

EXPOSE 8000