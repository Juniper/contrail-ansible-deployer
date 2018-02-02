FROM ubuntu:latest

MAINTAINER Pawel Kopka <pawel.kopka@codilime.com>

RUN apt-get update &&  \
    apt-get install -y bird  && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*


VOLUME ["/etc/multicloud/bird/"]
VOLUME ["/run/bird/"]

CMD ["bird"]
