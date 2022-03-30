# pull official base image
FROM python:3.9.6-alpine

RUN apk update && apk add build-base python3-dev gcc libc-dev libffi-dev zlib-dev jpeg-dev postgresql-dev musl-dev

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements/local.txt .
COPY ./requirements/base.txt .
RUN pip install -r local.txt

# copy entrypoint.sh
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

COPY . .

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]