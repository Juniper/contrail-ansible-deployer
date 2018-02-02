FROM ubuntu:latest

MAINTAINER Pawel Kopka <pawel.kopka@codilime.com>

ENV STRONGSWAN_VERSION 5.6.1

RUN apt-get update && \
    apt-get install -y \
        wget \
        tar \
        bzip2 \
        make \
        gcc \
        libgmp3-dev \
        kmod \
        iproute && \
    wget http://download.strongswan.org/strongswan-$STRONGSWAN_VERSION.tar.bz2 && \
    tar xjvf strongswan-$STRONGSWAN_VERSION.tar.bz2 && \
    ./strongswan-$STRONGSWAN_VERSION/configure --prefix=/usr --sysconfdir=/etc  && \
    make strongswan-$STRONGSWAN_VERSION/ && \
    make install strongswan-$STRONGSWAN_VERSION/ && \
    apt-get purge -y \
        wget \
        bzip2 \
        make \
        gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*  strongswan-$STRONGSWAN_VERSION

RUN ln -sf /etc/multicloud/strongswan/ipsec.conf /etc/ipsec.conf
RUN ln -sf /etc/multicloud/strongswan/ipsec.secrets /etc/ipsec.secrets
RUN ln -sf /etc/multicloud/strongswan/strongswan.conf /etc/strongswan.conf
RUN ln -sf /etc/multicloud/strongswan/stroke.conf /etc/strongswan.d/charon/stroke.conf
RUN ln -sf /etc/multicloud/ssl/CA.crt /etc/ipsec.d/cacerts/CA.crt
RUN ln -sf /etc/multicloud/ssl/HOST.crt /etc/ipsec.d/certs/HOST.crt
RUN ln -sf /etc/multicloud/ssl/HOST.key /etc/ipsec.d/private/HOST.key

VOLUME ["/etc/multicloud/strongswan/"]
VOLUME ["/etc/multicloud/ssl/"]

CMD ["ipsec"] 
