#!/bin/sh
sleep 5  # This is just to ensure the postgres is fully up and running.
python manage.py makemigrations
python manage.py migrate
# Recompile translations; with the repo mounted over /app, the image's compiled files are hidden
for po in $(find locale -name '*.po'); do msgfmt --check-format -o "${po%.po}.mo" "$po"; done
# python manage.py collectstatic --noinput
exec "$@"