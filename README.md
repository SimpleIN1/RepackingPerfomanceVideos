# RepackingVideos

WEB-app for repacking videos from BigBlueButton using ffmpeg on django.
Stack: Python, Django, Celery, Gunicorn, ffmpeg, NGINX, Docker, docker-compose, PostgreSQL, Redis

# DEBUG

---

## Redis

Install redis-server:

    sudo apt update
    sudo apt install redis-server

## Install requirements

Install python environments:  

    python -m venv venv

Activate venv:

    source venv/bin/activate

Install required packages:

    pip install -r requirements.txt

## Settings environments

Create file .env, configure environments and add envs to the .env file:

    touch .env

environments

    DEBUG=1
    ALLOWED_HOSTS=*
    INTERNAL_IPS=127.0.0.1
    CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://0.0.0.0:8000
    
    BBB_SHARED_SECRET=bbb_shared_secret
    BBB_RESOURCE=domain.ru
    BBB_URL=https://{0}/bigbluebutton/api/getRecordings?state=published
    
    EMAIL_HOST=smtp.mail.ru
    EMAIL_PORT=2525
    EMAIL_USE_TLS=1
    EMAIL_HOST_USER=email@mail.ru
    EMAIL_HOST_PASSWORD=password
    
    EMAIL_SENDER=1
    
    SCHEMA=http
    WEBSITE_NAME=project_name
    DOMAIN=localhost
    SUPPORT_EMAIL=test@mail.ru
    SUCCESS_ATTEMPT_COUNT=7
    
    NEXTCLOUD_RESOURCE=nextcloud.ru
    NEXTCLOUD_USER=user
    NEXTCLOUD_PASSWORD=password
    NEXTCLOUD_PATH=directory
    NEXTCLOUD_SHARE_LINK=https://nextcloud.ru/route
    NEXTCLOUD_SHARE_LINK_PASSWORD=password
    
    CACHE_REDIS=redis://localhost:6379/0
    
    CELERY_BROKER_URL=redis://localhost:6379/1
    CELERY_RESULT_BACKEND=redis://localhost:6379/1
    
    REDIS_HOST=localhost
    REDIS_PORT=6379
    REDIS_DB=2

    POSTGRES_PASSWORD=postgres_pass
    POSTGRES_DB=postgres_db
    POSTGRES_USER=postgres_user
    POSTGRES_PORT=5432
    POSTGRES_HOST=172.18.0.3

## Celery

Go to root directory of the app:

    cd RepachingProject/

Run celery worker (example) for ffmpeg queue to process video threads:

     celery -A CeleryApp.app worker --loglevel=debug -c 1 -Q ffmpeg_worker_queue

Run celery worker (example) for upload queue to upload files to the NextCloud:

     celery -A CeleryApp.app worker --loglevel=debug --concurrency=1 -Q upload_worker_queue

Run celery worker (example) for common queue to send email and remove directory:

    celery -A CeleryApp.app worker --beat --loglevel=debug --concurrency=4 -Q common_worker_queue

## Flower

Run flower for monitoring celery workers:
    
    flower --broker=redis://redis:6379/1 --port=5555 --basic-auth=user:pswd --url_prefix=flower

## Django app

Go to root directory of the app:

    cd RepachingProject/

Tests:

    pytest tests/[filename].py
    ./manage.py tests [app_label].tests

Migrations:

    ./manage.py makemigrations [app_label]
    ./manage.py migrate

Run application:

    ./manage.py runserver

# PROD

---

## Settings environments
Create .env files, configure environments and add envs to the .env files.

Create files:
    
    touch .docker.env .docker.posgres.env .docker.broker.env .docker.flower.env

file .docker.env:
    
    DEBUG=0
    ALLOWED_HOSTS=*
    INTERNAL_IPS=127.0.0.1
    CSRF_TRUSTED_ORIGINS=http://127.0.0.1:8000,http://0.0.0.0:8000
    
    BBB_SHARED_SECRET=bbb_shared_secret
    BBB_RESOURCE=domain.ru
    BBB_URL=https://{0}/bigbluebutton/api/getRecordings?state=published
    
    EMAIL_HOST=smtp.mail.ru
    EMAIL_PORT=2525
    EMAIL_USE_TLS=1
    EMAIL_HOST_USER=email@mail.ru
    EMAIL_HOST_PASSWORD=password
    
    EMAIL_SENDER=1
    
    SCHEMA=http
    WEBSITE_NAME=project_name
    DOMAIN=localhost
    SUPPORT_EMAIL=test@mail.ru
    SUCCESS_ATTEMPT_COUNT=7
    
    NEXTCLOUD_RESOURCE=nextcloud.ru
    NEXTCLOUD_USER=user
    NEXTCLOUD_PASSWORD=password
    NEXTCLOUD_PATH=directory
    NEXTCLOUD_SHARE_LINK=https://nextcloud.ru/route
    NEXTCLOUD_SHARE_LINK_PASSWORD=password
    
    CACHE_REDIS=redis://localhost:6379/0
    CELERY_RESULT_BACKEND=redis://localhost:6379/1
    
    REDIS_HOST=localhost
    REDIS_PORT=6379
    REDIS_DB=2
    
    FFMPEG_CELERY_CONCURRENCY=1

file .docker.postgres.env:

    POSTGRES_PASSWORD=postgres_pass
    POSTGRES_DB=postgres_db
    POSTGRES_USER=postgres_user
    POSTGRES_PORT=5432
    POSTGRES_HOST=0.0.0.0

file .docker.broker.env:

    CELERY_BROKER_URL=redis://redis:6379/1

file .docker.flower.env:

    FLOWER_BASIC_AUTH=user:pswd

file .docker.nginx.env

    SERVER_NAME=localhost
    SSL_CERTIFICATE_PATH=/etc/letsencrypt/localhost/localhost.crt
    SSL_CERTIFICATE_KEY_PATH=/etc/letsencrypt/localhost/localhost.key

file docker-certbot.env
    
    EMAIL=test@mail.ru
    SERVER_NAME=localhost

## Docker + Certbot

Run docker certbot service

    docker-compose -f docker-compose.certbot.yml --env-file docker-certbot.env up

## Docker

Docker build:
    
    docker-compose -f docker-compose.prod.yml up -d

Docker debug build:
    
    docker-compose -f docker-compose.dev.yml up -d

Run migrations in container:

    docker-compose -f docker-compose.prod.yml exec server ../venv/bin/python manage.py makemigration [AppName]
    docker-compose -f docker-compose.prod.yml exec server ../venv/bin/python manage.py migrate

Run create superuser in container:
    
    docker-compose -f docker-compose.prod.yml exec server ../venv/bin/python manage.py createsuperuser

Run load staticfiles to admin panel in container:
 
    docker-compose -f docker-compose.prod.yml exec server ../venv/bin/python manage.py collectstaic

Run uploading recording from a resource in container:
    
    docker-compose -f docker-compose.prod.yml exec server  ../venv/bin/python manage.py upload_recordings

## Letsencrypt certificate

Create letsencrypt certificate

    docker-compose -f docker-compose.certbot.yml up

Renew letsencrypt certificate
    
    docker compose run --rm certbot renew --dry-run # Test renewal
    docker compose run --rm certbot renew # Actual renewal