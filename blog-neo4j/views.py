from flask import Flask, render_template,\
     url_for, request, redirect, flash, \
     session
import os
from models import User, get_most_recent_posts, \
    Post, get_recent_posts, OutputPost, search_database

from werkzeug.utils import secure_filename


app = Flask(__name__)


app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
app.config["IMAGE_UPLOADS"] = "C:\\Users\\stvar\\python\\blog-neo4j\\static\\images"

def allowed_image(filename):

    if not "." in filename:
        return False

    ext = filename.rsplit(".", 1)[1]

    if ext.upper() in app.config["ALLOWED_IMAGE_EXTENSIONS"]:
        return True
    else:
        return False


@app.route('/')
def index():
    rp = get_recent_posts()
    recent_posts = []
    for p in rp:
        post = Post(p['id'])
        post_details = post.find()
        author = post.get_author()
        hashtags = post.get_hashtags()
        comments = post.get_comments()
        recent = OutputPost(post_details, author, hashtags, comments)
        recent_posts.append(recent)
    
    return render_template('index.html', recent_posts=recent_posts)


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
    image = User(viewed).get_my_image()

    my_posts = []
    for p in posts:
        post = Post(p['id'])
        post_details = post.find()
        author = post.get_author()
        hashtags = post.get_hashtags()
        comments = post.get_comments()
        my_post = OutputPost(post_details, author, hashtags, comments)
        my_posts.append(my_post)

    #image = image.replace(',', '\\')
    return render_template(
        'profile.html',
         username=viewed,
         my_posts = my_posts,
         image = image
         )


@app.route('/post/<post_id>')
def open_post(post_id):
    p = Post(post_id)
    selected_post = p.find()
    user = p.get_author()
    hashtags = p.get_hashtags()
    comments = p.get_comments()
    return render_template(
        'post.html',
        post=selected_post,
        user=user,
        hashtags=hashtags,
        comments=comments     
        )

@app.route('/add_comment/<post_id>', methods=['GET', 'POST'])
def new_comment(post_id):
    pid = post_id
    commentator = session['username']
    text = request.form['comment']
    if not text:
        flash('This blog prohibits silent comments')
    
    else:
        User(commentator).add_comment(pid, text)

    return redirect(url_for('index'))  


@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        old = request.form['old']
        new = request.form['new']
        confirm = request.form['confirm']

        if not User(session['username']).verify(old):
            flash('That is not your password')
        
        elif new != confirm:
            flash('New passwords do not match')

        else:
            User(session['username']).change_password(new)
            flash('Password successfully changed') 


    return render_template ('change_password.html')



@app.route('/change_profile_picture',  methods=['GET', 'POST'])
def change_profile_picture():
    image = User(session['username']).get_my_image()
    if request.method == "POST":

        if request.files:
            image = request.files["image"]

            if image.filename == "":
                return redirect(request.url)
            
            elif allowed_image(image.filename):
                filename = secure_filename(image.filename)
                path = os.path.join(app.config["IMAGE_UPLOADS"], session['username'])
                file = os.path.join(path, filename)
                
                if not os.path.isdir(path):
                    os.mkdir(path)

                if not os.path.isfile(file):
                    image.save(file)
                
                image_location = "\\static\\images\\" + session['username'] + "\\" + filename

                #print(image_location.replace(',', '\\'))
                User(session['username']).change_profile_picture(image_location)
                return redirect(request.url)

            else: 
                flash("You cannot upload that.")
                return redirect(request.url)

    return render_template('change_profile_picture.html', image=image)


@app.route('/similar_users')
def similar_users():
    similars = User(session['username']).get_similar_users()
    return render_template('similar_users.html', similars=similars)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        to_search = request.form['to_search']
        searched_posts, phh, users = search_database(to_search)
        
        posts = []
        for p in searched_posts:
            post = Post(p['id'])
            post_details = post.find()
            author = post.get_author()
            hashtags = post.get_hashtags()
            comments = post.get_comments()
            rp = OutputPost(post_details, author, hashtags, comments)
            posts.append(rp)
        
        posts_having_hashtags = []
        for ph in phh:
            post = Post(ph['id'])
            post_details = post.find()
            author = post.get_author()
            hashtags = post.get_hashtags()
            comments = post.get_comments()
            hashtag_post = OutputPost(post_details, author, hashtags, comments)
            posts_having_hashtags.append(hashtag_post)
        
        return render_template('search_results.html', posts=posts, posts_having_hashtags=posts_having_hashtags, users=users, to_search=to_search)

    else:    
        return render_template('search_page.html')


if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)