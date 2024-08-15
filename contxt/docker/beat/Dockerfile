FROM python:3.12-slim

ENV PYTHONDOWNWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY . /app
WORKDIR /app

RUN python -m venv /py && \
    apt-get update && \
    apt-get install -y postgresql-client && \
    apt-get install -y --no-install-recommends build-essential postgresql musl && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /app/requirements.txt && \
    apt-get purge -y --auto-remove build-essential postgresql musl && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password --no-create-home user

ENV PATH="/py/bin:$PATH"
USER user