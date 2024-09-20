FROM node:22-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN git clone --branch v5.2.0 --depth=1 https://github.com/twbs/bootstrap.git /bootstrap

COPY buildTheme.sh /buildTheme.sh
COPY oepstrap.scss /oepstrap.scss

RUN npm install -g sass@1.77.0

WORKDIR /

ENTRYPOINT ["/bin/bash", "/buildTheme.sh"]
