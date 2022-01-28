from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

Db = SQLAlchemy()

class Game(Db.Model):
    __tablename__ = 'games'
    gid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    rounds = Db.Column(Db.Integer)
    admin = Db.Column(Db.Integer)
  
class Question(Db.Model):
    __tablename__ = 'questions'
    qid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    word = Db.Column(Db.Text())
    phrase = Db.Column(Db.Text(), unique =True, nullable=False)

class QuestionsInUse(Db.Model):
    __tablename__ = 'questionsinuse'
    quid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    word1 = Db.Column(Db.Text(), nullable=False)
    phrase1 = Db.Column(Db.Text(), nullable=False)  
    word2 = Db.Column(Db.Text(), nullable=False)
    phrase2 = Db.Column(Db.Text(), nullable=False) 
    gid = Db.Column(Db.Integer, nullable=False)
    uid = Db.Column(Db.Integer, nullable=False)

class Response(Db.Model):
    __tablename__ = 'responses'
    rid = Db.Column(Db.Integer, primary_key=True, autoincrement=True)
    response1 = Db.Column(Db.Text())
    response2 = Db.Column(Db.Text())
    response3 = Db.Column(Db.Text())
    response4 = Db.Column(Db.Text())
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
    vote = Db.Column(Db.Integer)
    votequantity = Db.Column(Db.Integer)
    uid = Db.Column(Db.Integer)
    gid = Db.Column(Db.Integer)
