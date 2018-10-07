from flask import Flask, render_template, request, url_for, redirect
from flask import flash, jsonify
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models import Base, User, Subject
from flask import session as login_session
import random
import string

#IMPORTS REQUIRED FOR APPLYING OAuth2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
       open('client_secrets.json', 'r').read())['web']['client_id']
Application_NAME = "sudanMentors"

#connect to the database and create a dtabase session
engine = create_engine('sqlite:///studentsmentors.db?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
       state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                       for x in range(32))
       login_session['state'] = state
       return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST', 'GET'])
def gconnect():
       # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is'
                                 'already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    # login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['role'] = 'user'
    

    # see if a user exists, if not make a new one

    user_id = getUserID(login_session['email'])
    if not user_id:
            
        user_id = createUser(login_session)
        #createAdmin(login_session['email'])
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;'
    '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print 'In gdisconnect access token is %s', access_token
    print 'User name is: '
    print login_session['username']
    url = ('https://accounts.google.com/o/oauth2/revoke?token=%s'
           % login_session['access_token'])
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['role']
        
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for'
                                 'given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

# User Helper Functions

def createUser(login_session):
       newUser = User(name=login_session['username'], email=login_session[
                      'email'], picture=login_session['picture'],role=login_session['role'])
       session.add(newUser)
       session.commit()
       user = session.query(User).filter_by(email=login_session['email']).one()
       return user.id
def getUserInfo(user_id):
       user = session.query(User).filter_by(id=user_id).one
       return user

def getUserID(email):
       try:
              user = session.query(User).filter_by(email=email).one()
              return user.id
       except:
              return None
       
def createAdmin(email):
        try:
               if email=='raniana30@gmail.com':
                      user = session.query(User).filter_by(email=email).one()
                      user.role = 'admin'
                      session.add(user)
                      session.commit()
               return user.id
        except:
               return None

              
@app.route('/')
def showHome():
	#return("this page to show home page")
       return render_template('home.html')
@app.route('/welcome')
def welcome():
       return"welcome,click here to go to your page"
@app.route('/welcome/user')
def welcomeUser():
       userID=login_session['user_id']
       user = session.query(User).filter_by(id=userID).one()
       if user.role== 'user':
              return"You Are Not Registered Yet"
       elif user.role=='student':
              return render_template('studenPage.html',name=user.role)
       elif user.role=='mentor':
              return render_template('mentorPage.html')
@app.route('/admin/users')
def showUsers():
       users=session.query(User).all()
       if users:
              return render_template('showusers.html', users=users)
       else:
              return"there are no users to show"
@app.route('/admin/users/<int:userID>')
def showUser(userID):
       #return "this page is to show user informations"
       user=session.query(User).filter_by(id=userID).one()
       return render_template('showuser.html',user=user)
@app.route('/admin/users/<int:userID>/edit', methods=['GET','POST'])
def editUser(userID):
       userToEdit=session.query(User).filter_by(id=userID).one()
       if request.method=='POST':
              if request.form['role']:
                     userToEdit.role = request.form['role']
              session.add(userToEdit)
              session.commit()
              return redirect(url_for('showUser',userID=userToEdit.id))
       else:
              return render_template('edituser.html', user=userToEdit)
       
              
       
@app.route('/mentor/login')
def mentorLogin():
       return"this page will display a form for mentors to log in"
@app.route('/mentor')
def showMentor():
       return "this page will display mentor information along with the assosiated students"
@app.route('/mentor/add')
def addMentor():       
       return"this page is to add a mentor not sure yet by manager or by mentor"
@app.route('/mentor/delete')
def deleteMentor():
       return"this page is for deleting a mentor"

	
if __name__ == '__main__':
        app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host='0.0.0.0', port=8000)		
 
