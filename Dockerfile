FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt /app/

RUN mkdir reports && \
    pip install -r requirements.txt

COPY app /app/app/
COPY static /app/static/

CMD [ "python", "-m", "app.main" ]
