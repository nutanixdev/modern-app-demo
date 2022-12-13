# FROM gcr.io/paketo-buildpacks/builder:base

FROM quay.io/fedora/python-311

USER 0

ADD . /tmp/src
RUN /usr/bin/fix-permissions /tmp/src
USER 1001

# Install the dependencies
RUN /usr/libexec/s2i/assemble

# Set the default command for the resulting image
CMD /usr/libexec/s2i/run