FROM python:3.10.14

RUN apt-get update \
    && apt-get install -y apache2 apache2-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

RUN pip install mod_wsgi
RUN mod_wsgi-express module-config >> /etc/apache2/apache2.conf

COPY ./docker/apache2.conf /etc/apache2/conf-enabled/oeplatform.conf
COPY . /app
COPY ./docker/docker-entrypoint.sh /app/docker-entrypoint.sh

RUN mkdir -p /app/ontologies && cd /app/ontologies/ && wget https://github.com/OpenEnergyPlatform/ontology/releases/download/v2.5.0/build-files.zip && unzip build-files.zip
RUN mkdir -p /app/media/oeo_ext && cp /app/oeo_ext/oeo_extended_store/oeox_template/oeo_ext_template_empty.owl /app/media/oeo_ext/oeo_ext.owl

RUN cp /app/oeplatform/securitysettings.py.default /app/oeplatform/securitysettings.py && python manage.py collectstatic --noinput && rm /app/oeplatform/securitysettings.py

EXPOSE 80

CMD ["/bin/bash", "/app/docker-entrypoint.sh"]
