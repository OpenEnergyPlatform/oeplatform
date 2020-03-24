FROM node:13

COPY buildTheme.sh /buildTheme.sh
COPY oepstrap.scss /oepstrap.scss

RUN apt-get update && apt-get install -y \
    git \
    ruby-full \
 && rm -rf /var/lib/apt/lists/*

RUN git clone --branch v4.4.1 https://github.com/twbs/bootstrap.git /bootstrap
RUN gem install sass

WORKDIR /

ENTRYPOINT ["/bin/bash", "/buildTheme.sh"]