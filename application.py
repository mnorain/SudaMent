from flask import Flask, render_template
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
 
