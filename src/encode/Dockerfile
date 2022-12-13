FROM quay.io/fedora/python-311

USER 0

COPY . /tmp/src
RUN /usr/bin/fix-permissions /tmp/src

ADD https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz /tmp

RUN yum install -y xz \
    && tar -C /tmp/ -xf /tmp/ffmpeg-* \
    && mv /tmp/ffmpeg-*/ffmpeg /usr/local/bin/ \
    && rm -fR /tmp/ffmpeg-*
# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends xz-utils \
#     && apt-get autoremove -y && apt-get clean -y \
#     && tar -C /tmp/ -xf /tmp/ffmpeg-* \
#     && mv /tmp/ffmpeg-*/ffmpeg /usr/local/bin/ \
#     && rm -fR /tmp/ffmpeg-*

USER 1001

# Install the dependencies
RUN /usr/libexec/s2i/assemble

# Set the default command for the resulting image
CMD python -m parliament .