#!/bin/bash

# 데이터베이스 마이그레이션
python manage.py migrate

# 정적 파일 수집
python manage.py collectstatic --noinput

# cron 서비스 시작
service cron start

# Django 서버 시작
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000
