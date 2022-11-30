FROM --platform=linux/amd64 ntnxtme/mediainfo:base

USER root

ADD https://mediaarea.net/download/binary/mediainfo/22.09/mediainfo_22.09-1_amd64.xUbuntu_18.04.deb /tmp
ADD https://mediaarea.net/download/binary/libmediainfo0/22.09/libmediainfo0v5_22.09-1_amd64.xUbuntu_18.04.deb /tmp
ADD https://mediaarea.net/download/binary/libzen0/0.4.39/libzen0v5_0.4.39-1_amd64.xUbuntu_18.04.deb /tmp

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends libmediainfo0v5:amd64 \
    && apt-get autoremove -y && apt-get clean -y

RUN dpkg -i /tmp/*.deb \
    && rm -f /tmp/*.deb

USER 1000:1000