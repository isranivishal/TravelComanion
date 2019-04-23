from flask import Flask, render_template,request,redirect,url_for,logging,session
from pymongo import MongoClient
from bson.json_util import dumps
import json
from flask_bcrypt import Bcrypt
import numpy as np
import pandas as pd

# from .movies_recommender import get_top_movies_list,get_movie_recommendation,get_genre_list

client = MongoClient('127.0.0.1:27017')
db = client.travel_companion

app = Flask(__name__)
app.secret_key='mysecret'
bcrypt = Bcrypt(app)

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

def if_logged_in():
    if session['set']==1:
        return True
    else:
        return False     


# User Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        users=db.users
        existing_user = users.find_one({'email_id' : request.form['email_id'] })

        if existing_user is None:
            hashpass= bcrypt.generate_password_hash(request.form['password']).decode('utf-8')          
            id=users.count() + 1
            first_name = request.form['first_name']
            last_name = request.form['last_name']
            email_id = request.form['email_id']
            my_list={}
            my_list["books"]=[]
            my_list["movies"]=[]
            my_list["tv_shows"]=[]
            my_list["songs"]=[]
            purchases={}
            purchases["books"]=[]
            purchases["movies"]=[]
            purchases["tv_shows"]=[]
            purchases["songs"]=[]
            history={}
            history["books"]=[]
            history["movies"]=[]
            history["tv_shows"]=[]
            history["songs"]=[]

            users.insert_one({
                    "id" : id,
                    "first_name" : first_name,
                    "last_name" : last_name,
                    "email_id" : email_id,
                    "password" : hashpass,
                    "my_list" : my_list,
                    "purchases" : purchases,
                    "history" : history
            })
            session['id']=id
            session['set']=1
            return redirect(url_for('user_personalise'))
        return 'The user already exists!'
    return render_template('Home.html')

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    users=db.users
    login_user = users.find_one({'email_id' : request.form['email_id'] })
    if login_user:
        if bcrypt.check_password_hash(login_user['password'],request.form['password']):
            session['id']=login_user['id']
            session['set']=1
            return redirect(url_for('home')) 
    return 'Invalid Username/Password Combination'

@app.route('/home')
def home():
    names= db.users.find({'id' : session['id']},{'_id':0,'first_name' : 1 })
    for doc in names:
        for i in doc:
            name=doc[i]
    if(if_logged_in()):
        return render_template('home.html',name=name)
    else:
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear
    session['set']=0
    return redirect(url_for('index'))      

# get user related info

@app.route('/user_personalise')
def user_personalise():
    names= db.users.find({'id' : session['id']},{'_id':0,'first_name' : 1 })
    for doc in names:
        for i in doc:
            name=doc[i]
    return render_template('user-personalise.html',name=name)  

@app.route('/get_user_data', methods=['GET', 'POST'])
def get_user_data():
    
    books=[]
    movies=[]
    tvshows=[]
    songs=[]

    books.append(request.form['book1'])
    books.append(request.form['book2'])
    books.append(request.form['book3'])

    movies.append(request.form['movie1'])
    movies.append(request.form['movie2'])
    movies.append(request.form['movie3'])

    tvshows.append(request.form['tvshow1'])
    tvshows.append(request.form['tvshow2'])
    tvshows.append(request.form['tvshow3'])

    songs.append(request.form['songs1'])
    songs.append(request.form['songs2'])
    songs.append(request.form['songs3'])

    
    db.users.update_one(
            {"id": session['id']},
            {
                "$set": {
                    "history":{
                        "books" : books,
                        "movies" : movies,
                        "tv_shows" : tvshows,
                        "songs" : songs
                    }
                }
        }
    )
    return redirect(url_for('user_loading'))

@app.route('/user_loading')
def user_loading():
    names= db.users.find({'id' : session['id']},{'_id':0,'first_name' : 1 })
    for doc in names:
        for i in doc:
            name=doc[i]
    return render_template('user-loading.html',name=name)  

# user related 

@app.route('/my_list', methods = ['GET'])
def my_list():
    try:
        user_details = db.users.find({'id' : session['id']},{'_id':0,'my_list' : 1 })
        # for doc in user_details:
        #     for i in doc:
        #         items=doc[i]
        #         for i in items:
        #             a=items[i]
        #             for j in a:
        #                 print(j)    
    except Exception as e:
        return dumps({'error' : str(e)})
    return render_template('user-my-list.html', user_details=user_details)    

@app.route('/my_account', methods = ['GET'])
def my_account():
    try:
        user_details = db.users.find({'id' : session['id']},{'_id':0,'first_name' : 1,'last_name' : 1,'email_id' : 1,'history' : 1 })
        # for doc in user_details:
        #     for i in doc:
        #         items=doc[i]
        #         for i in items:
        #             a=items[i]
        #             for j in a:
        #                 print(j)    
    except Exception as e:
        return dumps({'error' : str(e)})
    return render_template('user-my-account.html', user_details=user_details)   

@app.route('/my_purchases', methods = ['GET'])
def my_purchases():
    try:
        user_details = db.users.find({'id' : session['id']},{'_id':0,'first_name' : 1,'last_name' : 1,'email_id' : 1,'purchases' : 1 })
        # for doc in user_details:
        #     for i in doc:
        #         items=doc[i]
        #         for i in items:
        #             a=items[i]
        #             for j in a:
        #                 print(j)    
    except Exception as e:
        return dumps({'error' : str(e)})
    return render_template('user-my-purchases.html', user_details=user_details)   

#modules routing

@app.route("/tvshow-home")
def tvshow_home():
    df=pd.read_csv('tvshow_metadata.csv', delimiter = ',')
    
    toplist=df['Title'].head(6).tolist()
    tv_show_details=[]
    for title in toplist:
        tv_show_details.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))
    
    most_popular_list=df.sort_values(by = ['imdbRating','Year'],ascending = False).head(6)
    tv_show_details1=[]
    for title in most_popular_list['Title'].tolist():
        tv_show_details1.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))
    
    less_time=df[(df.Runtime > 30) & (df.Runtime <60)].sort_values(by = ['imdbRating'],ascending= False).head(6)
    tv_show_details7=[]
    for title in less_time['Title'].tolist():
        tv_show_details7.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))

    more_time=df[(df.Runtime > 0) & (df.Runtime <30)].sort_values(by = ['imdbRating'],ascending= False).head(6)
    tv_show_details8=[]
    for title in more_time['Title'].tolist():
        tv_show_details8.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))

    indian_list=df.loc[df['Country'] == 'India'].sort_values(by = ['imdbRating'],ascending= False).head(6)
    tv_show_details2=[]
    for title in indian_list['Title'].tolist():
        tv_show_details2.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))
    
    romance_list=df[df["Genre"].str.contains('Romance',na=False)].sort_values(by = ['imdbRating','imdbVotes'],ascending= False).head(6)
    tv_show_details3=[]
    for title in romance_list['Title'].tolist():
        tv_show_details3.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))

    comedy_list=df[df["Genre"].str.contains('Comedy',na=False)].sort_values(by =['imdbRating','imdbVotes'],ascending= False).head(6)
    tv_show_details4=[]
    for title in comedy_list['Title'].tolist():
        tv_show_details4.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1}))
    
    action_list=df[df["Genre"].str.contains('Action',na=False)].sort_values(by =['imdbRating','imdbVotes'],ascending= False).head(6)
    tv_show_details5=[]
    for title in action_list['Title'].tolist():
        tv_show_details5.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1})) 

    action_list=df[df["Genre"].str.contains('Animation',na=False)].sort_values(by =['imdbRating','imdbVotes'],ascending= False).head(6)
    tv_show_details6=[]
    for title in action_list['Title'].tolist():
        tv_show_details6.append(db.tv_shows.find({'Title' : title},{'_id':0,'Title' : 1,'imdbRating' : 1 ,'Genre' : 1,'Plot' : 1 ,'Poster' : 1})) 

    return render_template('tvshow-home.html',tv_show_details=tv_show_details,tv_show_details1=tv_show_details1,tv_show_details2=tv_show_details2,tv_show_details3=tv_show_details3,tv_show_details4=tv_show_details4,tv_show_details5=tv_show_details5,tv_show_details6=tv_show_details6,tv_show_details7=tv_show_details7,tv_show_details8=tv_show_details8)  

@app.route("/tvshow_details/<name>")
def tvshow_details(name):
    tvshow_name=db.tv_shows.find({'Title' : name})
    return render_template('tvshow-details.html',tv_show_details=tvshow_name)

@app.route("/books_home")
def books_home():
    return render_template('books-home.html')

@app.route("/movies_home")
def movies_home():
    # movies=get_genre_list('Romance')
    # movies1=get_top_movies_list()
    # movies2=get_movie_recommendation('The Notebook')

    # print(movies)
    # print(movies1)
    # print(movies2)

    return render_template('movies-home.html')

@app.route("/songs_home")
def songs_home():
    return render_template('songs-home.html')

@app.route("/places-near-by")
def places_near_by():
    return render_template('places-to-visit.html')


# curd operations
@app.route("/get_all_data", methods = ['GET'])
def get_all_contact():
    try:
        users = db.users.find()
        return dumps(users)
    except Exception as e:
        return dumps({'error' : str(e)})

@app.route("/add_details")
def add_details():
    try:
        id=db.users.find().count()+1
        first_name = "Liam"
        last_name = "Pyane"

        if first_name and last_name:
            db.users.insert_one({
                "id" : id,
                "first_name" : first_name,
                "last_name" : last_name
            })
        return dumps({'message' : 'SUCCESS'})
    except Exception as e:
        return dumps({'error' : str(e)})

if __name__ == '__main__':
    app.run(debug = True, threaded = True)