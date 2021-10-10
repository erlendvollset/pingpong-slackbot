FROM python:3.10.0-buster

RUN pip3 install poetry

WORKDIR app
ENV PYTHONPATH=/app

ADD pyproject.toml /app/pyproject.toml
ADD poetry.lock /app/poetry.lock
RUN poetry export --without-hashes -f requirements.txt | pip3 install --force-reinstall -r /dev/stdin

ADD src /app/src

CMD python src/pingpong/main.py
