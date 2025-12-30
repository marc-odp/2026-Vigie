FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .

RUN apt -y update && \
    apt install -y fonts-dejavu && \
    rm -rf /var/lib/apt/lists/* && \
    pip install .

COPY app app/
COPY static static/

CMD [ "python", "-m", "app.main" ]
