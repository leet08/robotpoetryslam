from dotenv import load_dotenv
from flask import Flask, flash, render_template, request, url_for, redirect, jsonify, session
from models.models import Db, Game, User, Question, QuestionsInUse, Response, Vote
from forms.forms import CreateGame, EnterGame, PlayForm, VoteForm, RemoveUserForm
from os import environ
import os
import sys
import pyttsx3
from sqlalchemy import func, and_, or_, not_
import random
import numpy as np
from flask_heroku import Heroku
from PIL import Image, ImageFont, ImageDraw 

load_dotenv('.env')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/balderdash3'

# config upload file folder
IMG_FOLDER = os.path.join('static', 'img')
app.config['UPLOAD_FOLDER'] = IMG_FOLDER

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
app.secret_key = "secret_key"
Db.init_app(app)

# the empty default profile, also test1 first added to current game is user 1. should these be strings
testProfile = '1'
emptyProfile = '2'
adminProfile = '3'

#GET /
@app.route('/')

# GET & POST /create
@app.route('/create', methods=['GET', 'POST'])
def create():
    # Init form
    form = CreateGame()

    if request.method == 'POST':
        # create random seed int
        adminAccess = int(request.form.get("adminResults"))
        numberRounds = int(request.form.get("numberRounds"))
        game = Game(rounds = numberRounds, admin = adminAccess)
        Db.session.add(game)
        Db.session.commit()

        newGame = Game.query.order_by(-Game.gid).first() # can use just game?

        flash('Congratulations, you have created a new game! You can now login with a username. Here is your Game ID:')

        return render_template('create.html', form = form, title='Create', games = newGame)
    else:
        #all_games = Game.query.all()
        return render_template('create.html', form = form, title='Create', games = 0)

@app.route('/enter', methods=['GET', 'POST'])
def enter():

    form = EnterGame()

    if request.method == 'POST':
        # Init credentials from form request
        gameID = request.form['gameID']
        username = request.form['username']
        session['username'] = username	    
        session['gameID'] = gameID
        session['formstep'] = 1

        # show players to player1 waiting room?
        currentGame = Game.query.filter_by(gid=gameID).first()

        # check if they are already in the game and can reenter. query username and gid.
        possibleUsers = User.query.filter_by(gid=gameID)
        userFlag = False

        for p in possibleUsers: 
            if p.username == username:
                userFlag = True
                session['uid'] = p.uid
                session['room'] = p.roundnumber

        if userFlag == False and username != 'ADMIN':
            # create a new user
            user = User(username = username, gid = gameID, playernumber = 0, roundnumber = 1)
            Db.session.add(user)
            Db.session.commit()

            # add to the game 
            currentPlayers = User.query.filter_by(gid=gameID)
            currentPlayerNumber = 0

            # add up player numbers to get current player number
            for p in currentPlayers:
                if p.playernumber != 0:
                    currentPlayerNumber = currentPlayerNumber + 1

            user.playernumber = currentPlayerNumber + 1
            Db.session.add(user)
            Db.session.add(currentGame)

            # create new questions in questions in use DB for each user
            numberRounds = currentGame.rounds

            newUserQuestion1 = Question.query.order_by(func.random())[:numberRounds]
            for i in range(numberRounds):
                word1 = newUserQuestion1[i].word
                phrase1 = newUserQuestion1[i].phrase

            newUserQuestion2 = Question.query.order_by(func.random())[:numberRounds]
            if (newUserQuestion2 != newUserQuestion1):
                for i in range(numberRounds):
                    word2 = newUserQuestion2[i].word
                    phrase2 = newUserQuestion2[i].phrase
                    
            Db.session.add(QuestionsInUse(word1 = word1, phrase1 = phrase1, word2 = word2, phrase2 = phrase2, gid = currentGame.gid, uid = user.uid))
            Db.session.commit()

            # assign to session uid
            session['uid'] = user.uid
            session['room'] = 1
            Db.session.commit()

        if username == 'ADMIN':
            session['uid'] = adminProfile
            session['room'] = 1
            Db.session.commit()

        # list for waiting room in order
        players = User.query.filter_by(gid=gameID).order_by(User.playernumber)

        #flash('Congratulations, you have entered a game')
        return render_template('waiting.html', title='Waiting', players = players, session_username=username, session_game =gameID, room = session['room'])
    else:
        return render_template('enter.html', form = form, title='Enter')  

@app.route('/waiting')
def waiting():
    # Control by login status
    if 'username' in session:
        session_uid = User.query.filter_by(uid=session['uid']).first()
        session_game = Game.query.filter_by(gid=session['gameID']).first()

        # which waiting room (1-3) for if reconnecting
        room = session['room']

        return render_template('waiting.html', title='Waiting', room = room, players = [" "], session_username=session_uid.username, session_game=session_game)
    else:
        #all_posts = Post.query.all()
        return render_template('waiting.html', title='Waiting', room = room, players = [" "], session_username=session_uid.username, session_game=session_game)

def get_count(q):
    count_q = q.statement.with_only_columns([func.count()]).order_by(None)
    count = q.session.execute(count_q).scalar()
    return count

# GET & POST /play
@app.route('/play', methods=['GET', 'POST'])
def play():
    # Init form
    form = PlayForm()

    # Init user by Db query to user and to game?
    #user = User.query.filter_by(username=username).first()
    session_user = User.query.filter_by(uid=session['uid']).first()
    session_game = Game.query.filter_by(gid=session['gameID']).first()

    questions = QuestionsInUse.query.filter_by(gid = session['gameID'], uid = session['uid'])
    numQuestions = get_count(questions)

    formNames = []
    responses = []
    for i in range(numQuestions):
        stringResponse = "response" + str(i+1)
        formNames.append(stringResponse)

    if session['uid'] == adminProfile:
        players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
        return render_template('waiting.html', title='Waiting', session_game = session_game.gid, numQuestions = numQuestions, players = players, session_username=session_user.username, form = form, room = 2)
    

    # first button enters response and reveals next line
    if request.method == 'POST':

        if session['formstep'] == 1:
            # Create responses in database
            for i in range(numQuestions):
                formResponse = request.form.get(formNames[i], None)
                totalResponse1 = questions[i].phrase1 + ' ' + formResponse
                session['response1']=totalResponse1

            session['formstep'] = 2
            return render_template('play2.html', title='Play2', response = totalResponse1, game = session_game, questions = questions, numQuestions = numQuestions, session_username=session_user.username, form = form, formStep = session['formstep'])

        if session['formstep'] == 2:
            # Create responses in database
            for i in range(numQuestions):
                formResponse = request.form.get(formNames[i], None)
                totalResponse2 = formResponse
                session['response2']=totalResponse2

            session['formstep'] = 3
            return render_template('play3.html', title='Play3', game = session_game, questions = questions, numQuestions = numQuestions, session_username=session_user.username, form = form, formStep = session['formstep'])

        if session['formstep'] == 3:
            # Create responses in database
            for i in range(numQuestions):
                formResponse = request.form.get(formNames[i], None)
                totalResponse3 = questions[i].phrase2 + ' ' + formResponse
                session['response3']=totalResponse3

            session['formstep'] = 4
            return render_template('play4.html', title='Play4', response = totalResponse3, game = session_game, questions = questions, numQuestions = numQuestions, session_username=session_user.username, form = form, formStep = session['formstep'])

        if session['formstep'] == 4:
            # Create responses in database
            for i in range(numQuestions):
                formResponse = request.form.get(formNames[i], None)
                totalResponse4 = formResponse

            newResponse = Response(response1=session['response1'],response2 = session['response2'], response3 = session['response3'], response4 = totalResponse4, uid=session['uid'], gid=session['gameID'], quid = questions[i].quid)
            Db.session.add(newResponse)
            Db.session.commit()

            # Generate picture and TTS

            # randomly choose one of 6 backgrounds and text locations
            rand = random.randrange(1,6,1)

            # also generate filename and text
            #newGame = Response.query.order_by(-Game.gid).first() # can use just game?
            
            text1 = session['response1'] +'\n'+session['response2'] +'\n'+session['response3'] +'\n'+totalResponse4

            if rand == 1:
                my_image = Image.open("resources/robot1.jpg")
                font = ImageFont.truetype("resources/Darling.ttf", 24)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((55,65), text1, (0, 0, 0), font=font)

            if rand == 2:
                my_image = Image.open("resources/robot2.jpg")
                font = ImageFont.truetype("resources/unicode.futurab.ttf", 28)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((65,85), text1, (255, 255, 255), font=font)

            if rand == 3:
                my_image = Image.open("resources/robot3.jpg")
                font = ImageFont.truetype("resources/unicode.futurab.ttf", 28)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((45,85), text1, (255, 255, 255), font=font)

            if rand == 4:
                my_image = Image.open("resources/robot4.jpg")
                font = ImageFont.truetype("resources/unicode.futurab.ttf", 28)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((65,85), text1, (1, 50, 32), font=font)

            if rand == 5:
                my_image = Image.open("resources/robot5.jpg")
                font = ImageFont.truetype("resources/unicode.futurab.ttf", 28)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((45,385), text1, (255, 200, 0), font=font)

            if rand == 6:
                my_image = Image.open("resources/robot6.jpg")
                font = ImageFont.truetype("resources/unicode.futurab.ttf", 28)
                image_editable = ImageDraw.Draw(my_image)
                image_editable.text((65,425), text1, (50, 50, 50), font=font)

            filename = str(newResponse.rid) + ".jpg"
            file_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            my_image.save(file_filename)

            # Generate TTS
            text2 = session['response1'] +'...'+session['response2'] +'...'+session['response3'] +'...'+totalResponse4
            engine = pyttsx3.init()
            #engine.say("I will speak this text")
            engine.setProperty('rate', 150) # default 200
            if rand < 4:
                engine.setProperty('voice', 'english-us')
            if rand >=4:
                engine.setProperty('voice', 'english_rp+f3') 
            filenameMp3 = os.path.join(app.config['UPLOAD_FOLDER'],str(newResponse.rid)+".mp3")
            engine.save_to_file(text2, filenameMp3)
            engine.runAndWait()

            # update round number for player
            session_user.roundnumber = 2
            Db.session.add(session_user)
            session['room'] = 2
            Db.session.commit()

            # show players to player1 waiting room
            players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)

            return render_template('waiting.html', title='Waiting', session_game = session_game.gid, numQuestions = numQuestions, players = players, session_username=session_user.username, form = form, room = 2)
    else:
        return render_template('play.html', title='Play', game = session_game, questions = questions, numQuestions = numQuestions, session_username=session_user.username, form = form, formStep = session['formstep'])

def getR(player, question):
    return Response.query.filter_by(uid = player.uid, qid = question.qid)

def getV(player, question):
    return Vote.query.filter_by(uid = player.uid, qid = question.qid)

# GET & POST /voting
@app.route('/voting', methods=['GET', 'POST'])
def voting():
    # Init form
    form = VoteForm()

    # Init user by Db query to user and to game?
    #user = User.query.filter_by(username=username).first()
    session_user = User.query.filter_by(uid=session['uid']).first()
    session_game = Game.query.filter_by(gid=session['gameID']).first()

    # call all responses assigned to this game, get all players and all questions also
    # only 1 question for now...
    responses = Response.query.filter_by(gid=session['gameID'])
    responsesCount = get_count(responses)
    players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
    playerCount = get_count(players)
    
    rids = []
    filenames = []
    filenameMp3s = []
    responseTexts = []

    # get filenames
    for i in range(responsesCount):
        rid = responses[i].rid
        rids.append(rid)
        responseTexts.append(responses[i].response1 +'... ' + responses[i].response2 +"... " + responses[i].response3 +"... " + responses[i].response4)
        full_filename = os.path.join(app.config['UPLOAD_FOLDER'], str(rid)+'.jpg')
        filenames.append(full_filename)
        full_filenameMp3 = os.path.join(app.config['UPLOAD_FOLDER'], str(rid)+'.mp3')
        filenameMp3s.append(full_filenameMp3)

    if request.method == 'POST':

        if session['uid'] != adminProfile:
            # Get field button values and query vote was for which player's response and enter to vote database
            # each vote records the player number receiving the vote and quantity
            stringVote = "voting" + str(0 + 1)
            stringVote = int(request.form.get(stringVote, None))
            if stringVote != 0:
                vote = Vote(vote = stringVote-1,votequantity = 1, uid = session_user.uid, gid = session_game.gid)
                Db.session.add(vote)

            # update round number for player
            session_user.roundnumber = 3
            session['room'] = 3
            Db.session.add(session_user)
            Db.session.commit()

        return render_template('waiting.html', title='Waiting', playerCount = playerCount, players = players, session_game = session_game.gid, session_username=session_user.username, form = form, room = 3)
    else:
        return render_template('voting.html', title='Voting', responseTexts = responseTexts, players = players, filenames = filenames, filenameMp3s = filenameMp3s, playerCount = playerCount,game = session_game, session_username=session_user.username, form = form)

@app.route('/results', methods=['GET'])
def results():
    # Control by login status
    if 'username' in session :
        session_uid = User.query.filter_by(uid=session['uid']).first()
        session_game = Game.query.filter_by(gid=session['gameID']).first()

        # Get votes and my player number
        votes = Vote.query.filter_by(gid = session['gameID'])
        myPlayerNumber = session_uid.playernumber

        # add score to user
        score = 0
        for v in votes:
            if v.vote == myPlayerNumber:
                score = score + 1
        session_uid.score = score
        Db.session.add(session_uid)
        Db.session.commit()

        return render_template('results.html', title='Results',  session_username=session_uid.username, game=session_game)
    else:
        #all_posts = Post.query.all()
        return render_template('results.html', title='Results', session_username=session_uid.username, game=session_game)

@app.route('/results2', methods=['GET'])
def results2():
    # Control by login status
    if 'username' in session:
        session_uid = User.query.filter_by(uid=session['uid']).first()
        session_game = Game.query.filter_by(gid=session['gameID']).first()
        #posts = Post.query.filter_by(author=session_user.uid).all()

        # Get each question, responses, votes
        responses = Response.query.filter_by(gid=session['gameID'])
        responsesCount = get_count(responses)
        players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
        playerCount = get_count(players)
        questions = QuestionsInUse.query.filter_by(gid = session['gameID'])
        questionCount = get_count(questions)
        votes = Vote.query.filter_by(gid = session['gameID'])

        # get filenames
        responseTexts = []
        filenames = []
        for i in range(responsesCount):
            responseTexts.append(responses[i].response1 +'... ' + responses[i].response2 +"... " + responses[i].response3 +"... " + responses[i].response4)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], str(responses[i].rid)+'.jpg')
            filenames.append(full_filename)

        # points calculation
        highPlayerScore = 0
        highPlayer=[]
        tie = False
        for p in players:
            if p.score is None:
                p.score = 0
            if p.score > highPlayerScore:
                highPlayerScore = p.score # find high score
        for p in players: # find ties
            if p.score == highPlayerScore:
                highPlayer.append(p.username)
        if len(highPlayer) >1:
            tie = True 
        
        return render_template('results2.html', title='Results', filenames = filenames, playerCount = playerCount, numQuestions = questionCount,tie = tie, highPlayerScore = highPlayerScore, highPlayer = highPlayer, players = players, session_username=session_uid.username, game=session_game)
    else:
        #all_posts = Post.query.all()
        return render_template('results2.html', title='Results', session_username=session_uid.username, game=session_game)

# GET & POST /removeuser
@app.route('/removeuser', methods=['GET', 'POST'])
def removeuser():

    # Init form
    form = RemoveUserForm()

    session_uid = User.query.filter_by(uid=session['uid']).first()
    session_game = Game.query.filter_by(gid=session['gameID']).first()
    #posts = Post.query.filter_by(author=session_user.uid).all()

    players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)

    # which waiting room (1-3) for if reconnecting
    room = session['room']

    if request.method == 'POST':
        # Get field button values and query vote was for which player's response
        removeuser_entry = int(request.form.get("remove"))
        removeuser_player = players[removeuser_entry-1]
        removeuser_player.gid = 0

        Db.session.add(removeuser_player)
        Db.session.commit()

        return render_template('waiting.html', title='Waiting', room = 1, players = players, session_username=session_uid.username, session_game=session_game.gid)
    else:
        #all_posts = Post.query.all()
        return render_template('waiting.html', title='Waiting', room = room, players = players, session_username=session_uid.username, session_game=session_game.gid)

# POST /logout
@app.route('/logout', methods=['POST'])
def logout():
    # Logout
    session.clear()
    return redirect(url_for('enter'))







  
