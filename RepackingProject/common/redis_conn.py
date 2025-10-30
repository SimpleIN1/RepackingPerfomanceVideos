from django.conf import settings

import redis


def get_redis_connection():
    r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
    return r
