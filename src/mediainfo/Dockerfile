FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

USER 1001

WORKDIR $APP_HOME
COPY . ./

USER 0

ADD https://mediaarea.net/download/binary/mediainfo/22.09/mediainfo_22.09-1_amd64.xUbuntu_18.04.deb /tmp
ADD https://mediaarea.net/download/binary/libmediainfo0/22.09/libmediainfo0v5_22.09-1_amd64.xUbuntu_18.04.deb /tmp
ADD https://mediaarea.net/download/binary/libzen0/0.4.39/libzen0v5_0.4.39-1_amd64.xUbuntu_18.04.deb /tmp

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends libmediainfo0v5:amd64 \
    && apt-get autoremove -y && apt-get clean -y

RUN dpkg -i /tmp/*.deb \
    && rm -f /tmp/*.deb

RUN pip install --no-cache-dir -r requirements.txt

USER 1001

# Set the default command for the resulting image
CMD python -m parliament .