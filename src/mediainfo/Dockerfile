FROM quay.io/fedora/python-311

USER 0

COPY . /tmp/src
RUN /usr/bin/fix-permissions /tmp/src

# ADD https://mediaarea.net/download/binary/mediainfo/22.09/mediainfo_22.09-1_amd64.xUbuntu_18.04.deb /tmp
# ADD https://mediaarea.net/download/binary/libmediainfo0/22.09/libmediainfo0v5_22.09-1_amd64.xUbuntu_18.04.deb /tmp
# ADD https://mediaarea.net/download/binary/libzen0/0.4.39/libzen0v5_0.4.39-1_amd64.xUbuntu_18.04.deb /tmp

# RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
#     && apt-get -y install --no-install-recommends libmediainfo0v5:amd64 \
#     && apt-get autoremove -y && apt-get clean -y

# RUN dpkg -i /tmp/*.deb \
#     && rm -f /tmp/*.deb

RUN yum install -y mediainfo

USER 1001

# Install the dependencies
RUN /usr/libexec/s2i/assemble

# Set the default command for the resulting image
CMD python -m parliament .