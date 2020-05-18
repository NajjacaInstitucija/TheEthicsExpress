from flask import Flask, render_template,\
     url_for, request, redirect, flash, \
     session
import os
from models import User, get_most_recent_posts


app = Flask(__name__)

@app.route('/')
def index():
    posts = get_most_recent_posts()
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmed = request.form['confirm']
        
        if len(username) < 1:
            flash('Username cannot be empty')
        
        elif len(password) < 1:
            flash('Password cannot be empty')
        
        elif password != confirmed:
            flash('Passwords do not match')
        
        elif not User(username).register(password):
            flash('Username already exists')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
    
        if not User(username).verify(password):
            flash('Invalid username or password')

        else:
            session['username'] = username
            flash('Registration successful')
            return redirect(url_for('index'))
    
    return render_template('login.html') 


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/new_post', methods=['GET', 'POST'])
def new_post():
    header = request.form['header']
    hashtags = request.form['hashtags']
    body = request.form['body']

    if not header:
        flash('Posting without header is just stupid')
    
    elif not body:
        flash('Posting nothing. How fun')
    
    else:
        User(session['username']).new_post(header, hashtags, body)
    
    return redirect(url_for('index'))

@app.route('/profile/<username>')
def profile(username):
    viewed = username
    posts = User(viewed).get_my_posts()
    return render_template(
        'profile.html',
         username=viewed,
         posts = posts
         )



if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)