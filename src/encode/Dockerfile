FROM --platform=linux/amd64 ntnxtme/encode:base

USER root

ADD https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz /tmp

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends xz-utils \
    && apt-get autoremove -y && apt-get clean -y \
    && tar -C /tmp/ -xf /tmp/ffmpeg-* \
    && mv /tmp/ffmpeg-*/ffmpeg /usr/local/bin/ \
    && rm -fR /tmp/ffmpeg-*

USER 1000:1000