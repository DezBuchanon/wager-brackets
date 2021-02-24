import pyrebase
import os
import json

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, make_response

#insert firebase config

firebase = pyrebase.initialize_app(firebaseConfig)

db=firebase.database()
auth=firebase.auth()
storage=firebase.storage()

#SEARCH FUNCTION
#search = db.child("users").order_by_child("isHost").equal_to(True).get()
#print(search.val())

app = Flask(__name__)

picFolder = os.path.join('static', 'img')

app.config['UPLOAD_FOLDER'] = picFolder

@app.route("/", methods=["POST", "GET"])
def index():
    if request.method == "POST":
        email = request.form["email"]
        psw = request.form["pass"]
        auth.sign_in_with_email_and_password(email,psw)

        currentUser = auth.current_user
        userID = currentUser["localId"]

        return redirect(url_for('profile', user_id=userID))
    else:
        return render_template("index.html")

@app.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")
    else:
        email = request.form["email"]
        psw = request.form["pass"]
        usrn = request.form["username"]
        confirm = request.form["confirm"]

        if psw == confirm:
            auth.create_user_with_email_and_password(email,psw)
            auth.sign_in_with_email_and_password(email,psw)
            user = auth.current_user
            setId = user["localId"]
            data = {'userName': usrn, 'isHost': False, 'numOfPlayers': 0, 'activeTournament': "???"}
            db.child("users").child(setId).set(data)
            return redirect(url_for('profile', user_id=setId))
        else:
            #error handle needed for failed confirmed password
            return render_template("signup.html")


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    else:
        email = request.form["email"]
        psw = request.form["pass"]
        auth.sign_in_with_email_and_password(email,psw)

        currentUser = auth.current_user
        userID = currentUser["localId"]

        return redirect(url_for('profile', user_id=userID))

@app.route("/profile/<user_id>", methods=["POST", "GET"])
def profile(user_id):
    if request.method == "GET":
        currentUser = auth.current_user
        userID = currentUser["localId"]
        userName = db.child("users").child(userID).child("userName").get().val()
        activeTournament = db.child("users").child(userID).child("activeTournament").get().val()

        return render_template("profile.html", userName = userName, activeTournament = activeTournament)
    else:
        return render_template("profile.html", user = auth.current_user)

@app.route("/createtournament", methods=["POST", "GET"])
def createtournament():
    if request.method == "GET":
        return render_template("createtournament.html", )
    else:
        currentUser = auth.current_user
        userID = currentUser["localId"]
        numOfPlayers = int(request.form["numOfPlayers"])

        #creates an empty list of players in tournament
        players = {}

        for x in range(numOfPlayers):
            players["player{}".format(x)] = {'userName': "???", 'resultsIn': False, 'winner': False, 'uid': "???"}
            
        db.child("users").child(userID).child("tournament").set(players)

        #updates host tournament status
        host = db.child("users").child(userID).child("userName").get().val()
        data = {'numOfPlayers': numOfPlayers, 'isHost': True, 'activeTournament': userID }
        db.child("users").child(userID).update(data)

        #sets first player to host
        hostName = {'userName': host, 'uid': userID}
        db.child("users").child(userID).child("tournament").child("player0").update(hostName)

        return redirect(url_for('profile', user_id=userID))

@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "GET":
        search = db.child("users").order_by_child("isHost").equal_to(True).get()
        return render_template("search.html", search=search)

@app.route("/tournament/<host_id>", methods=["POST", "GET"])
def tournament(host_id):
    if request.method == "GET":
        currentUser = auth.current_user
        userID = currentUser["localId"]
        userName = db.child("users").child(userID).child("userName").get().val()
        tournament = db.child("users").child(host_id).child("tournament").get()
        host = db.child("users").child(host_id).child("userName").get().val()
            
        return render_template("tournament.html", host=host, host_id=host_id, userID=userID, userName=userName, tournament=tournament)
    else:
        req = request.get_json()
        tournament = db.child("users").child(host_id).child("tournament").get().val()
        currentUser = auth.current_user
        userID = currentUser["localId"]
        userName = db.child("users").child(userID).child("userName").get().val()
        numOfPlayers = len(tournament)
        host = db.child("users").child(host_id).child("userName").get().val()

        #handles submit win request
        if next(iter(req)) == "win_yes":
            results = {'resultsIn': True, 'winner': True}
            for player in tournament:
                if tournament[player]['uid'] == userID:
                    db.child("users").child(host_id).child("tournament").child(player).update(results)

        #handles submit lose request
        if next(iter(req)) == "win_no":
            results = {'resultsIn': True, 'winner': False}
            for player in tournament:
                if tournament[player]['uid'] == userID:
                    db.child("users").child(host_id).child("tournament").child(player).update(results)
        
        #evaluates whether all players have submitted results and deletes all losers
        if next(iter(req)) == "declare_winner":
            resultsIn = 0
            winner = ""
            for player in tournament:
                if tournament[player]['resultsIn'] == True:
                    resultsIn = resultsIn + 1
            if resultsIn ==  numOfPlayers:
                for player in tournament:
                    if tournament[player]['winner'] == False:
                        playerID = tournament[player]['uid']
                        data = {'activeTournament': '???'}
                        db.child("users").child(playerID).update(data)
                        db.child("users").child(host_id).child("tournament").child(player).remove()
                    if tournament[player]['winner'] == True:
                        results = {'resultsIn': False, 'winner': False}
                        db.child("users").child(host_id).child("tournament").child(player).update(results)
                print(winner)
            else:
                print("All results are not in")            

        return render_template("tournament.html")

@app.route("/viewtournament/<host_id>", methods=["POST", "GET"])
def viewTournament(host_id):
    if request.method == "GET":
        currentUser = auth.current_user
        userID = currentUser["localId"]
        userName = db.child("users").child(userID).child("userName").get().val()
        tournament = db.child("users").child(host_id).child("tournament").get()
        host = db.child("users").child(host_id).child("userName").get().val()
            
        return render_template("viewtournament.html", host=host, host_id=host_id, userID=userID, userName=userName, tournament=tournament)
    else:
        req = request.get_json()
        tournament = db.child("users").child(host_id).child("tournament").get().val()
        currentUser = auth.current_user
        userID = currentUser["localId"]
        userName = db.child("users").child(userID).child("userName").get().val()
        emptySeats = 0

        print(next(iter(req)))
        #handles join request
        if next(iter(req)) == "join":
            #finds 1st empty player seat and fills it with currentUser
            for player in tournament:
                if tournament[player]['uid'] == '???':
                    newPlayer = {'userName': userName, 'uid': userID}
                    db.child("users").child(host_id).child("tournament").child(player).update(newPlayer)
                    break

            #sets active tournament
            activeTournament = { 'activeTournament': host_id}
            db.child("users").child(userID).update(activeTournament)

            #searchs for empty seats if only one is found tournament is rendered unviewable in search
            for player in tournament:
                if tournament[player]['uid'] == '???':
                    emptySeats = emptySeats + 1
            
            #makes tournament unviewable in search
            if emptySeats == 1:
                fullTourney = {'isHost': False}
                db.child("users").child(host_id).update(fullTourney)

        return redirect(url_for('tournament', host_id=host_id))

if __name__ == "__main__":
    app.run(debug=True)

    
