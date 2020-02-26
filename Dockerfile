FROM python:3.6-slim-buster

ARG SSH_PRIVATE_KEY
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ssh gcc python-dev

RUN mkdir /root/.ssh
# remember to use a temporary variable for this
# This private key shouldn't be saved in env files
RUN echo "${SSH_PRIVATE_KEY}" >> /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa
RUN cat /root/.ssh/id_rsa
RUN tr ' ' '\n' < /root/.ssh/id_rsa
RUN cat /root/.ssh/id_rsa
# make sure your domain is accepted
RUN touch /root/.ssh/known_hosts
RUN cat /root/.ssh/id_rsa
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts
RUN eval `ssh-agent -s` && ssh-add /root/.ssh/id_rsa


COPY . /code/
WORKDIR /code/

EXPOSE 8000