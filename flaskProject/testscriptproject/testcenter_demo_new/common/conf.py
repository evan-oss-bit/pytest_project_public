import os
import logging
import time
from logging.handlers import RotatingFileHandler as LogHandler

home_path = os.environ["HOME_PATH"] = os.path.split(os.path.realpath(__file__))[0]
print(home_path)


def getcwd(path_file, root_path=home_path):
    if os.name == "nt":
        path_file = path_file.replace("/", "\\")
    elif os.name == "posix":
        path_file = path_file.replace("\\\\", "/").replace("\\", "/")
    temp = os.path.join(root_path, path_file)
    return temp


def log_config(f_level=logging.INFO, c_level=logging.CRITICAL, out_path='', filename='info', fix=False):
    logfile = os.path.join(out_path, filename) + '-' + time.strftime('%Y_%m%d_%H%M%S', time.localtime()) + '.log' \
        if not fix else os.path.join(out_path, filename) + '.log'
    logger = logging.getLogger(logfile)
    logger.setLevel(f_level)

    fh = LogHandler(logfile, maxBytes=100 * 1024 * 1024, backupCount=50)
    fh.setLevel(f_level)

    ch = logging.StreamHandler()
    ch.setLevel(c_level)

    formatter = logging.Formatter('[%(levelname)s]--%(asctime)s--[%(filename)s %(funcName)s %(lineno)d]: %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger, logfile
