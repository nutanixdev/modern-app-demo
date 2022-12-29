FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

USER 1001

WORKDIR $APP_HOME
COPY . ./

USER 0

ADD https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz /tmp

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends xz-utils \
    && apt-get autoremove -y && apt-get clean -y \
    && tar -C /tmp/ -xf /tmp/ffmpeg-* \
    && mv /tmp/ffmpeg-*/ffmpeg /usr/local/bin/ \
    && rm -fR /tmp/ffmpeg-*

RUN pip install --no-cache-dir -r requirements.txt

USER 1001

# Set the default command for the resulting image
CMD python -m parliament .