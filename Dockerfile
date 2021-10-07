FROM python:3.7.12-slim-buster

RUN pip3 install poetry

WORKDIR app
ENV PYTHONPATH=/app

ADD pyproject.toml /app/pyproject.toml
ADD poetry.lock /app/poetry.lock
RUN poetry export --without-hashes -f requirements.txt | pip3 install --force-reinstall -r /dev/stdin

ADD pingpong /app/pingpong

CMD python pingpong/slackbot.py

