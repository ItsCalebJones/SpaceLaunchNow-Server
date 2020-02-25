FROM python:3.6-slim-buster

ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY ./requirements.txt /code/requirements.txt

# remember to use a temporary variable for this
# This private key shouldn't be saved in env files
RUN echo "${SSH_PRIVATE_KEY}" >> /root/.ssh/id_rsa && chmod 600 /root/.ssh/id_rsa
# make sure your domain is accepted
RUN touch /root/.ssh/known_hosts
RUN ssh-keyscan github.com >> /root/.ssh/known_hosts

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ssh gcc python-dev  \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r /code/requirements.txt \
    && apt-get purge -y --auto-remove git gcc python-dev

COPY . /code/
WORKDIR /code/

EXPOSE 8000