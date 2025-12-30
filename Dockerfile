FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml .

RUN mkdir reports && \
    pip install .

COPY app app/
COPY static static/

CMD [ "python", "-m", "app.main" ]
