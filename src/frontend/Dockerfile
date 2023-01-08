FROM mcr.microsoft.com/vscode/devcontainers/python:3.11-bullseye

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

USER 1001

WORKDIR $APP_HOME
COPY . ./

USER 0

RUN pip install --no-cache-dir -r requirements.txt

RUN python manage.py collectstatic

USER 1001

EXPOSE 8080

# Set the default command for the resulting image
CMD gunicorn --bind :8080 --workers 3 base.wsgi