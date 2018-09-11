from flask import Flask, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Subject

#IMPORTS REQUIRED FOR APPLYING OAuth2
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

#connect to the database and create a dtabase session
engine = create_engine('sqlite:///studentsmentors.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()
@app.route('/')
def showHome():
	#return("this page to show home page")
       return render_template('home.html')
	
if __name__ == '__main__':
	app.debug = True
	app.run(host='0.0.0.0', port=8000)		
 
