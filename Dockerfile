FROM python:3.8-slim-bullseye

WORKDIR /app
COPY requirements/base.txt ./requirements/base.txt
COPY requirements/local.txt ./requirements/local.txt
COPY requirements/production.txt ./requirements/production.txt

ENV DJANGO_DEBUG=True
#ENV DJANGO_SECRET_KEY='THISISMYSECRETKEYTOSEIFITALLWORKS'
ENV DJANGO_ALLOWED_HOSTS='*'
ENV ALLOWED_HOSTS='*'
ENV DJANGO_SETTINGS_MODULE='config.settings.local'


RUN apt update && apt install -y curl
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
RUN apt install -y nodejs python3-dev libpq-dev gcc
RUN pip install --no-cache-dir -r requirements/local.txt
RUN pip install --no-cache-dir -r requirements/production.txt
RUN pip install gunicorn

COPY . .

RUN npm install
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
CMD ["gunicorn", "--preload", "-b", "0.0.0.0:6000", "config.wsgi:application", "--threads", "4", "-w", "4"]


