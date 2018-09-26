FROM python:3.7.0-slim

RUN apt-get update && apt-get install --assume-yes git

RUN pip3 install pipenv

RUN mkdir /app

WORKDIR /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN set -ex && pipenv install --deploy --system

COPY gateway /app/gateway/
COPY config/cpg_configuration_default.yml /app/config/cpg_configuration_default.yml

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD curl --fail http://localhost:8080/ping || exit 1

CMD ["python3", "-m", "gateway"]
