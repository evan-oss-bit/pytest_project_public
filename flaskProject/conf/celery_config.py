#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import os
from datetime import timedelta

from celery.schedules import crontab

# Celery 4 later uses BROKER_URL instead of CELERY_BROKER_URL.
CELERY_BROKER_URL = os.getenv("PYTEST_TOOL_CELERY_BROKER_URL", "amqp://guest:guest@localhost:5672//")
result_backend = os.getenv("PYTEST_TOOL_CELERY_RESULT_BACKEND", "redis://localhost:6379/15")
CELERY_ENABLE_UTC = False
timezone = 'Asia/Shanghai'
# 指定任务序列化方式
task_serializer = 'msgpack'
# 指定结果序列化方式
result_serializer = 'msgpack'
# 任务过期时间,celery任务执行结果的超时时间
result_expires = 60 * 20
# 指定任务接受的序列化类型.
accept_content = ["msgpack"]
# 任务发送完成是否需要确认，这一项对性能有一点影响
task_acks_late = True
# 压缩方案选择，可以是zlib, bzip2，默认是发送没有压缩的数据
task_compression = 'zlib'
# 规定完成任务的时间
# CELERYD_TASK_TIME_LIMIT = 5  # 在5s内完成任务，否则执行该任务的worker将被杀死，任务移交给父进程
# celery worker的并发数，默认是服务器的内核数目,也是命令行-c参数指定的数目
worker_concurrency = 4
# celery worker 每次去rabbitmq预取任务的数量
worker_prefetch_multiplier = 4
# 每个worker执行了多少任务就会死掉，默认是无限的
worker_max_tasks_per_child = 40
# 设置默认的队列名称，如果一个消息不符合其他的队列就会放在默认队列里面，如果什么都不设置的话，数据都会发送到默认的队列中
task_default_queue = "default"
# 设置详细的队列
task_queues = {
    "default": {  # 这是上面指定的默认队列
        "exchange": "default",
        "exchange_type": "direct",
        "routing_key": "default"
    },
    "topicqueue": {  # 这是一个topic队列 凡是topictest开头的routing key都会被放到这个队列
        "routing_key": "topic.#",
        "exchange": "topic_exchange",
        "exchange_type": "topic",
    },
    "task_eeg": {  # 设置扇形交换机
        "exchange": "tasks",
        "exchange_type": "fanout",
        "binding_key": "tasks",
    },
    
}
beat_schedule = {
    'task1': {
        'task': 'app.async_worker.task_time.monitor_viper_heart',
        # "schedule": timedelta(seconds=30),
        "schedule": crontab(minute="*/60"),
        "args": '',
    },
    'task2': {
        'task': 'app.async_worker.task_time.monitor_RTSP_online',
        # "schedule": timedelta(seconds=30),
        "schedule": crontab(minute="*/2"),
        "args": '',
    },
    'task3': {
        'task': 'app.async_worker.task_time.monitor_sc_heart',
        # "schedule": timedelta(seconds=30),
        "schedule": crontab(minute="*/60"),
        "args": '',
    },
    'task4': {
        'task': 'app.async_worker.task_time.monitor_rtsp_heart',
        # "schedule": timedelta(seconds=30),
        "schedule": crontab(minute="*/720"),
        "args": '',
    },
    # 'task2': {
    #     'task': 'app.tasks.test_task1',
    #     "schedule": timedelta(seconds=3),
    #     "args": '',
    # },
}
