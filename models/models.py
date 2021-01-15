from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

Db = SQLAlchemy()

class Game(Db.Model):
    __tablename__ = 'games'
    gid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    seed = Db.Column(Db.Integer)
    admin = Db.Column(Db.Integer)
  
class Question(Db.Model):
    __tablename__ = 'questions'
    qid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    category = Db.Column(Db.Text())
    question = Db.Column(Db.Text(), unique =True, nullable=False)
    correct = Db.Column(Db.Text(), nullable=False)  

class QuestionsInUse(Db.Model):
    __tablename__ = 'questionsinuse'
    quid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    question = Db.Column(Db.Text(), unique =True, nullable=False)
    correct = Db.Column(Db.Text(), nullable=False)  
    gid = Db.Column(Db.Integer, nullable=False)
    category = Db.Column(Db.Text(), nullable=False)

class Response(Db.Model):
    __tablename__ = 'responses'
    rid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    response = Db.Column(Db.Text())
    uid = Db.Column(Db.Integer)
    gid = Db.Column(Db.Integer)
    quid = Db.Column(Db.Integer)

class User(Db.Model):
    __tablename__ = 'users'
    uid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    username = Db.Column(Db.Text(), nullable=False)
    gid = Db.Column(Db.Integer)
    playernumber = Db.Column(Db.Integer)
    score = Db.Column(Db.Integer)
    roundnumber = Db.Column(Db.Integer)

class Vote(Db.Model):
    __tablename__ = 'votes'
    vid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    vote = Db.Column(Db.Text())
    uid = Db.Column(Db.Integer)
    gid = Db.Column(Db.Integer)
    quid = Db.Column(Db.Integer)
