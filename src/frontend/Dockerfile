FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

USER 1001

WORKDIR $APP_HOME
COPY . ./

USER 0

RUN pip install --no-cache-dir -r requirements.txt

USER 1001

RUN python manage.py collectstatics

EXPOSE 8080

# Set the default command for the resulting image
CMD gunicorn --bind :8080 --workers 3 base.wsgi