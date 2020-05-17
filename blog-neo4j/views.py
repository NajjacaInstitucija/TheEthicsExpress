from flask import Flask, render_template,\
     url_for, request, redirect, flash, \
     session
import os
from models import User


app = Flask(__name__)

@app.route('/')
def index():
    posts = ''
    return render_template('index.html', posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if len(username) < 1:
            flash('Username cannot be empty')
        
        elif len(password) < 1:
            flash('Password cannot be empty')
        
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
            return redirect(url_for('index'))
    
    return render_template('login.html') 

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)