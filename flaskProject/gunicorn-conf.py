import multiprocessing
import os
import platform

import gevent.monkey

gevent.monkey.patch_all()
debug = False
# 设置日志记录水平
loglevel = 'info'
# 服务地址（address:port）
bind = '0.0.0.0:5400'

if platform.system() == 'Windows':
    # win机器路径
    log_path = os.path.join(os.path.dirname(__file__), 'logs')
else:
    # 服务器路径
    log_path = 'logs'

# 设置进程文件目录
pidfile = log_path + '/gunicorn.pid'
logfile = log_path + '/gunicorn.log'
# 设置访问日志和错误信息日志路径
accesslog = log_path + '/gunicorn_access.log'
errorlog = log_path + '/gunicorn_error.log'

# 设置守护进程,将进程交给 supervisor 管理
daemon = 'false'
# 工作模式协程、默认 sync
worker_class = 'gevent'
# 启动的进程数（获取服务器的 cpu核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1
# 指定每个工作者的线程数
# threads = 20
# 设置最大并发量
worker_connections = 2000

x_forwarded_for_header = 'X-FORWARDED-FOR'