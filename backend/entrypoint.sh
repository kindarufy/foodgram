#!/bin/sh
set -e

if [ "$DB_ENGINE" = "django.db.backends.postgresql" ]; then
  echo "Ожидание PostgreSQL $DB_HOST:$DB_PORT..."
  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 1
  done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_ingredients
python manage.py load_tags

if [ "$LOAD_DEMO_DATA" = "true" ]; then
  python manage.py load_demo_data
fi

exec gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
