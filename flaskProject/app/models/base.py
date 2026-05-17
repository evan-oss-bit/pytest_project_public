from app import db
import datetime


# class Base(db.Model):
#     __abstract__ = True
#     id = db.Column(db.Integer, primary_key=True, index=True)
#     created_time = db.Column(db.DateTime, default=db.func.current_timestamp())
#     updated_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
class Base(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, index=True)
    created_time = db.Column(db.DateTime, default=datetime.datetime.now)
    updated_time = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
