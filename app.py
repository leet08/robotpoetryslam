from dotenv import load_dotenv
from flask import Flask, flash, render_template, request, url_for, redirect, jsonify, session
from models.models import Db, Game, User, Question, QuestionsInUse, Response, Vote
from forms.forms import CreateGame, EnterGame, PlayForm, VoteForm, RemoveUserForm
from os import environ
import sys
from passlib.hash import sha256_crypt
from sqlalchemy import func, and_, or_, not_
import random
import numpy as np
from flask_heroku import Heroku

load_dotenv('.env')

app = Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost/balderdash2'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
app.secret_key = "secret_key"
Db.init_app(app)

# the empty default profile, also test1 first added to current game is user 1. should these be strings
testProfile = '1'
emptyProfile = '2'
adminProfile = '3'
blankQuestion = '79' # word category
randomSeed = 0

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
        numberWordQuestions = int(request.form.get("wordQuestions"))
        numberMovieQuestions = int(request.form.get("movieQuestions"))
        numberLawQuestions = int(request.form.get("lawQuestions"))
        randomSeed = np.random.randint(100)
        game = Game(seed = randomSeed, admin = adminAccess)
        Db.session.add(game)
        Db.session.commit()

        newGame = Game.query.order_by(-Game.gid).first() # can use just game?

        # create new questions in questions in use DB
        # shuffle in each category
        newWordQuestions = Question.query.filter_by(category="word").order_by(func.random())[:numberWordQuestions]
        for i in range(numberWordQuestions):
            Db.session.add(QuestionsInUse(question = newWordQuestions[i].question, correct = newWordQuestions[i].correct, gid = newGame.gid, category = newWordQuestions[i].category))

        newMovieQuestions = Question.query.filter_by(category="movie").order_by(func.random())[:numberWordQuestions]
        for i in range(numberMovieQuestions):
            Db.session.add(QuestionsInUse(question = newMovieQuestions[i].question, correct = newMovieQuestions[i].correct, gid = newGame.gid, category = newMovieQuestions[i].category))

        newLawQuestions = Question.query.filter_by(category="law").order_by(func.random())[:numberLawQuestions]
        for i in range(numberLawQuestions):
            Db.session.add(QuestionsInUse(question = newLawQuestions[i].question, correct = newLawQuestions[i].correct, gid = newGame.gid, category = newLawQuestions[i].category))

        Db.session.commit()
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

    questions = QuestionsInUse.query.filter_by(gid = session_game.gid)
    numQuestions = get_count(questions)

    formNames = []
    responses = []
    for i in range(numQuestions):
        stringResponse = "response" + str(i+1)
        formNames.append(stringResponse)

    if request.method == 'POST':
        # Create responses in database
        for i in range(numQuestions):
            formResponse = request.form.get(formNames[i], None)
            responses.append(Response(response=formResponse,uid=session['uid'], gid=session['gameID'], quid = questions[i].quid))

        if session['uid'] != adminProfile:
            for r in responses:
                Db.session.add(r)

            # update round number for player
            session_user.roundnumber = 2
            Db.session.add(session_user)
            session['room'] = 2
            Db.session.commit()

        # show players to player1 waiting room
        players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)

        return render_template('waiting.html', title='Waiting', session_game = session_game.gid, numQuestions = numQuestions, players = players, session_username=session_user.username, form = form, room = 2)
    else:
        return render_template('play.html', title='Play', game = session_game, questions = questions, numQuestions = numQuestions, session_username=session_user.username, form = form)

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
    responses = Response.query.filter_by(gid=session['gameID'])
    players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
    playerCount = get_count(players)
    questions = QuestionsInUse.query.filter_by(gid = session['gameID'])
    questionCount = get_count(questions)

    # arrange responses in 2D array, questinons x players plus correct answers
    responseArray = np.empty((questionCount, playerCount+1), dtype="U244")
    ridArray = np.zeros((questionCount, playerCount+1))
    for i in range(questionCount):
        responseArray[i,playerCount] = questions[i].correct
        ridArray[i,playerCount] = 0 # correct answer uid
        for j in range(playerCount):
            # get the most recent entries
            responseArray[i,j] = Response.query.filter_by(uid= players[j].uid, quid = questions[i].quid).order_by(-Response.rid).first().response
            ridArray[i,j] = Response.query.filter_by(uid= players[j].uid, quid = questions[i].quid).order_by(-Response.rid).first().rid
    
    # randomize each row by game seed
    gameSeed = session_game.seed
    np.random.seed(gameSeed)
    for i in range(questionCount):
        np.random.shuffle(responseArray[i,:])
        
    np.random.seed(gameSeed)
    for i in range(questionCount):
        np.random.shuffle(ridArray[i,:])

    if request.method == 'POST':

        if session['uid'] != adminProfile:
            # Get field button values and query vote was for which player's response and enter to vote database
            for i in range(questionCount):
                stringVote = "voting" + str(i + 1)
                stringVote = int(request.form.get(stringVote, None))
                ridVote = ridArray[i,stringVote-1]
                if ridVote == 0:
                    vote = 0
                else:
                    personVote = Response.query.filter_by(rid = ridVote).first()
                    vote = personVote.uid
                    vote = User.query.filter_by(uid = vote).first()
                    vote = vote.playernumber
                vote = Vote(vote = vote,uid = session_user.uid, gid = session_game.gid, quid = questions[i].quid)
                Db.session.add(vote)

            # update round number for player
            session_user.roundnumber = 3
            session['room'] = 3
            Db.session.add(session_user)
            Db.session.commit()

        return render_template('waiting.html', title='Waiting', playerCount = playerCount, players = players, session_game = session_game.gid, session_username=session_user.username, form = form, room = 3)
    else:
        return render_template('voting.html', title='Voting', playerCount = playerCount,numQuestions = questionCount, questions = questions, responses = responseArray, game = session_game, session_username=session_user.username, form = form)

@app.route('/results', methods=['GET'])
def results():
    # Control by login status
    if 'username' in session :
        session_uid = User.query.filter_by(uid=session['uid']).first()
        session_game = Game.query.filter_by(gid=session['gameID']).first()

        # Get each question, responses, votes
        responses = Response.query.filter_by(gid=session['gameID'])
        players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
        playerCount = get_count(players)
        questions = QuestionsInUse.query.filter_by(gid = session['gameID'])
        questionCount = get_count(questions)
        votes = Vote.query.filter_by(gid = session['gameID'])

        # arrange responses in 2D array, questinons x players plus correct answers
        # put together results posts text
        responseArray = np.empty((questionCount, playerCount+1), dtype="U244")
        myVotesArray = np.empty((questionCount, playerCount+1), dtype="U244")
        myVotes = np.zeros(questionCount, dtype="int")
        yourVotes = np.empty(questionCount, dtype="U24")
        myPoints = np.zeros(questionCount, dtype="int")
        allVotes = Vote.query.filter_by(uid = session['uid'], gid = session['gameID'])
        yourScore = 0
        if session['uid'] != adminProfile:
            for i in range(questionCount):
                responseArray[i,playerCount] = "Correct answer: " + questions[i].correct
                # check your votes
                if allVotes[i].vote == 0:
                    yourVotes[i] = "the correct answer!"
                    myPoints[i] = myPoints[i] + 2
                    yourScore = yourScore + 2
                if allVotes[i].vote != 0:
                    #yourVotes[i] = yourVotes[i].vote
                    whoYouVotedFor = User.query.filter_by(gid = session['gameID'], playernumber = allVotes[i].vote).first()
                    yourVotes[i] = whoYouVotedFor.username
                for j in range(playerCount):
                    # get the most recent entries
                    responseArray[i,j] = players[j].username + ": "+Response.query.filter_by(uid= players[j].uid, quid = questions[i].quid).order_by(-Response.rid).first().response
                    # if it's a vote for me
                    if Vote.query.filter_by(uid = players[j].uid, quid = questions[i].quid).first().vote == session_uid.playernumber:
                        myVotesArray[i,j] = players[j].username
                        myVotes[i] = myVotes[i]+1
                        myPoints[i] = myPoints[i] + 1
                        yourScore = yourScore + 1

            # add score to user
            session_uid.score = yourScore
            Db.session.add(session_uid)
            Db.session.commit()

        return render_template('results.html', title='Results', numQuestions = questionCount, myPoints = myPoints, myVotesArray = myVotesArray, myVotes = myVotes, yourVotes = yourVotes, responses = responseArray, questions = questions, session_username=session_uid.username, game=session_game)
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
        players = User.query.filter_by(gid=session['gameID']).order_by(User.playernumber)
        playerCount = get_count(players)
        questions = QuestionsInUse.query.filter_by(gid = session['gameID'])
        questionCount = get_count(questions)
        votes = Vote.query.filter_by(gid = session['gameID'])

        # put together text posts
        responseArray = np.empty((questionCount, playerCount+1), dtype="U244")
        allVotesArray = np.empty((questionCount, playerCount), dtype="U244")
        for i in range(questionCount):
            responseArray[i,playerCount] = "Correct answer: " + questions[i].correct
            for j in range(playerCount):
                # get the most recent entries
                responseArray[i,j] = players[j].username + ": "+Response.query.filter_by(uid= players[j].uid, quid = questions[i].quid).order_by(-Response.rid).first().response
                vote = Vote.query.filter_by(uid = players[j].uid, quid = questions[i].quid).first().vote
                if vote != 0:
                    allVotesArray[i,j] = User.query.filter_by(gid = session['gameID'], playernumber = vote).first().username
                else:
                    allVotesArray[i,j] = ""

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
        
        return render_template('results2.html', title='Results', playerCount = playerCount, allVotesArray = allVotesArray, questions = questions, numQuestions = questionCount, responses = responseArray,tie = tie, highPlayerScore = highPlayerScore, highPlayer = highPlayer, players = players, session_username=session_uid.username, game=session_game)
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







  
