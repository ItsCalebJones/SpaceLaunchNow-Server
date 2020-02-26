FROM python:3.6-slim-buster

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ssh gcc python-dev

# remember to use a temporary variable for this
# This private key shouldn't be saved in env files
RUN mkdir /.ssh
RUN echo "${SSH_PRIVATE_KEY}" >> /.ssh/id_rsa && chmod 600 /.ssh/id_rsa
# make sure your domain is accepted
RUN touch /.ssh/known_hosts
RUN ssh-keyscan github.com >> /.ssh/known_hosts



COPY . /code/
WORKDIR /code/

EXPOSE 8000