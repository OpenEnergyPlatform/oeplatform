FROM python:3.7.10

RUN apt-get update \
    && apt-get install -y apache2 apache2-dev libapache2-mod-wsgi-py3\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app


COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY ./docker/apache2.conf /etc/apache2/conf-enabled/oeplatform.conf

COPY . /app

RUN python manage.py collectstatic

EXPOSE 80

CMD ["/usr/sbin/apache2ctl", "-DFOREGROUND"]