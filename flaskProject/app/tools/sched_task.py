# !/usr/bin/python3.8
# -*- coding: utf-8 -*-
from apscheduler.schedulers.background import BackgroundScheduler
from config import jobstores, executors
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR


def listerner(event):
    if event.exception:
        print('定时任务出现异常！')
    else:
        print('任务正常运行中...')


print("定时任务启动")
sched = BackgroundScheduler(jobstores=jobstores, executors=executors)
sched.add_listener(listerner, EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)

try:
    sched.start()
except Exception as e:
    print("定时任务启动异常：", e)
