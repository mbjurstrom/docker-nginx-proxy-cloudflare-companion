FROM tiredofit/alpine:3.6
MAINTAINER Mikael Bjurström <bjurstrom dot mikael at outlook dot com>

### Set Environment Variables
    ENV ENABLE_CRON=false \
        ENABLE_SMTP=false

### Dependencies
    RUN apk update && \
        apk add \
            python2 \
            py2-pip \
            && \

        pip install \
            cloudflare \
            docker \
            && \

### Cleanup
        rm -rf /root/.cache && \
        rm -rf /var/cache/apk/*

### Add Files
COPY scripts/cloudflare-companion.py ./scripts/cloudflare-companion.py

CMD [ "python", "-u","./scripts/cloudflare-companion.py" ]