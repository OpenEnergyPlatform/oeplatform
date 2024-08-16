FROM python:3.11.9

RUN apt-get update \
    && apt-get install -y apache2 apache2-dev libapache2-mod-wsgi-py3\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./docker/apache2.conf /etc/apache2/conf-enabled/oeplatform.conf
COPY . /app
COPY ./docker/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN mkdir -p /app/ontologies/oeo/2.4.0 && cd /app/ontologies/oeo/2.4.0 && wget https://github.com/OpenEnergyPlatform/ontology/releases/download/v2.4.0/build-files.zip && unzip build-files.zip && rm build-files.zip

RUN cp /app/oeplatform/securitysettings.py.default /app/oeplatform/securitysettings.py && python manage.py collectstatic --noinput && rm /app/oeplatform/securitysettings.py

EXPOSE 80

CMD ["/bin/bash", "/app/docker-entrypoint.sh"]
