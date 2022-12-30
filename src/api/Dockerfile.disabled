FROM python:3.11-slim

ENV PYTHONUNBUFFERED True

ENV APP_HOME /app

USER 1001

WORKDIR $APP_HOME
COPY . ./

USER 0

RUN pip install --no-cache-dir -r requirements.txt

USER 1001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]