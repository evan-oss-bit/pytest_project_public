# -*- coding: utf-8 -*-
import os
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor, \
    ProcessPoolExecutor


def _load_local_env():
    env_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".env")
    if not os.path.isfile(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_local_env()

redis_host = os.getenv("PYTEST_TOOL_REDIS_HOST", "127.0.0.1")
redis_port = int(os.getenv("PYTEST_TOOL_REDIS_PORT", "6379"))
task_redis_db = int(os.getenv("PYTEST_TOOL_REDIS_DB", "3"))
home_path = os.environ["HOME_PATH"] = os.path.split(os.path.realpath(__file__))[0]

report_path = os.path.join(home_path, "report")
logs = os.path.join(home_path, "logs")
testscriptproject = os.path.join(home_path, "testscriptproject")
config_name = "data.ini"
run_info = {"port": "5400", "ip": '0.0.0.0'}

# home_path = os.environ.get("HOME_PATH") if "HOME_PATH" in os.environ.keys() else \
#     os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + os.path.sep + "..")
# home_path = os.environ["HOME_PATH"] = os.getcwd().replace("\\", "//")

REDIS = {
    'host': redis_host,
    'port': redis_port,
    'db': task_redis_db
}
jobstores = {
    'redis': RedisJobStore(**REDIS),
}
executors = {
    'default': ThreadPoolExecutor(10),
    'processpool': ProcessPoolExecutor(5)
}


class AppConFig(object):
    # Database URL. Defaults to the bundled SQLite database for local startup.
    # MySQL example:
    # PYTEST_TOOL_DATABASE_URL=mysql+pymysql://root:password@127.0.0.1:3306/database?charset=utf8mb4
    sql_url = os.getenv("PYTEST_TOOL_DATABASE_URL") or f'sqlite:///{os.path.join(home_path, "db", "database.db")}'
    email_info = {
        "email_host": os.getenv("PYTEST_TOOL_EMAIL_HOST", ""),
        "token": os.getenv("PYTEST_TOOL_EMAIL_TOKEN", ""),
        "smtp": os.getenv("PYTEST_TOOL_EMAIL_SMTP", "smtp.qq.com"),
    }

    @staticmethod
    def is_sqlite(db_path=None):
        return str(db_path or AppConFig.sql_url).startswith("sqlite")

    @staticmethod
    def sqlalchemy_engine_options(db_path=None):
        if not AppConFig.is_sqlite(db_path):
            return {}
        return {
            "connect_args": {
                "timeout": 30,
                "check_same_thread": False,
            },
            "pool_pre_ping": True,
        }


def _sqlite_db_dir(db_url):
    if not str(db_url).startswith("sqlite:///"):
        return ""
    db_file = str(db_url).replace("sqlite:///", "", 1)
    if db_file in ("", ":memory:"):
        return ""
    return os.path.dirname(db_file)


def ensure_runtime_dirs():
    dirs = [
        report_path,
        logs,
        testscriptproject,
        os.path.join(home_path, "db"),
        os.path.join(home_path, "files"),
        os.path.join(home_path, "material"),
    ]
    sqlite_dir = _sqlite_db_dir(AppConFig.sql_url)
    if sqlite_dir:
        dirs.append(sqlite_dir)
    for item in dirs:
        if item:
            os.makedirs(item, exist_ok=True)


def configure_sqlite_engine(engine):
    if not str(engine.url.drivername).startswith("sqlite"):
        return
    if getattr(engine, "_pytest_tool_sqlite_configured", False):
        return
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    engine._pytest_tool_sqlite_configured = True


def db_work(db_path=""):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_path, **AppConFig.sqlalchemy_engine_options(db_path))
    configure_sqlite_engine(engine)
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    session.expunge_all()
    return session
