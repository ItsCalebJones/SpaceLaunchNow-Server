FROM python:3.6-slim-buster as base

ARG SSH_PRIVATE_KEY
ENV PYTHONUNBUFFERED 1
ENV DJANGO_ENV dev
ENV DOCKER_CONTAINER 1
COPY ./requirements /code/requirements
COPY ./requirements.txt /code/requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends git ssh gcc python-dev

ARG EXTRA_INDEX_URL
RUN pip config set global.extra-index-url "${EXTRA_INDEX_URL}"

RUN rm -rf /var/lib/apt/lists/* \
    && pip install -r /code/requirements.txt \
    && apt-get purge -y --auto-remove git gcc python-dev


COPY . /code/
WORKDIR /code/

EXPOSE 8000

FROM base as web
CMD ["gunicorn"  , "-b", ":8000", "spacelaunchnow.wsgi", "--workers", "3"]

FROM base as celeryworker
CMD sh -c "celery -A spacelaunchnow worker --loglevel=INFO"

FROM base as celerybeat
CMD sh -c "celery -A spacelaunchnow beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"

FROM base as api
ENV IS_WEBSERVER=False
ENV IS_API=True
CMD ["gunicorn"  , "-b", ":8000", "spacelaunchnow.wsgi", "--workers", "3"]

FROM base as discordbot
CMD bash -c "python /code/bot.py"