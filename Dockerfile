FROM python:3.6-slim-buster

ARG SSH_PRIVATE_KEY
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY src/requirements /code/requirements
COPY src/requirements.txt /code/requirements.txt


RUN apt-get update && apt-get install -y --no-install-recommends git ssh gcc python-dev

ARG EXTRA_INDEX_URL
RUN pip config set global.extra-index-url "${EXTRA_INDEX_URL}"

RUN rm -rf /var/lib/apt/lists/* \
    && pip install -r /code/requirements.txt \
    && apt-get purge -y --auto-remove git gcc python-dev


COPY src/ /code/
WORKDIR /code/

EXPOSE 8000