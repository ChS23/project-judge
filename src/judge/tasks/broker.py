from taskiq_redis import ListQueueBroker

from judge.settings import settings

broker = ListQueueBroker(url=settings.redis_url)
