from flask import Flask, render_template,\
     url_for, request, redirect, flash, \
     session
import os, sys
from models import User, get_most_recent_posts, \
    Post, get_recent_posts, OutputPost, search_database, Comment

from werkzeug.utils import secure_filename


app = Flask(__name__)


app.config["ALLOWED_IMAGE_EXTENSIONS"] = ["JPEG", "JPG", "PNG", "GIF"]
#app.config["IMAGE_UPLOADS"] = "C:\\Users\\stvar\\python\\blog-neo4j\\static\\images"
dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
dirname = dirname.replace("\\","/")
app.config["IMAGE_DELETIONS"] = dirname
app.config["IMAGE_UPLOADS"] = os.path.join(dirname + '/', 'static/images')

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
            flash('Login successful')
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
    #body = request.form['body']
    body = request.form.get("body")
    body2 = body.split('\n')
    new_body = ''.join(['<br>' + line for line in body2])
    body = new_body

    post_pics = []
    
    if request.files:    
        for pic in request.files.getlist("pics"):
            if pic.filename == "":
                continue
            
            elif allowed_image(pic.filename):
                filename = secure_filename(pic.filename)
                short_path = os.path.join(app.config["IMAGE_UPLOADS"] + '/', session['username'])
                path = os.path.join(short_path + '/', "post")
                file = os.path.join(path + '/', filename)
                
                if not os.path.isdir(short_path):
                    os.mkdir(short_path)

                if not os.path.isdir(path):
                    os.mkdir(path)

                if not os.path.isfile(file):
                    pic.save(file)
                
                #pic_location = "\\static\\images\\" + session['username'] + "\\post\\" + filename
                pic_location = "/static/images/" + session['username'] + "/post/" + filename
                post_pics.append(pic_location)

            else: 
                flash("You cannot upload that picture")


    if not header:
        flash('Posting without header is just stupid')
    
    elif not body:
        flash('Posting nothing. How fun')
    
    else:
        User(session['username']).new_post(header, hashtags, body, post_pics)
    
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
    if request.method == 'POST':
        pid = post_id
        commentator = session['username']
        #text = request.form['comment']
        text = request.form.get("comment")
        text2 = text.split('\n')
        new_text = ''.join(['<br>' + line for line in text2])
        text = new_text
        if not text:
            flash('This blog prohibits silent comments')
    
        else:
            User(commentator).add_comment(pid, text)

    return open_post(post_id)  


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
                short_path = os.path.join(app.config["IMAGE_UPLOADS"] + '/', session['username'])
                path = os.path.join(short_path + '/', "profile")
                file = os.path.join(path + '/', filename)

                if not os.path.isdir(short_path):
                    os.mkdir(short_path)
                
                if not os.path.isdir(path):
                    os.mkdir(path)

                if not os.path.isfile(file):
                    image.save(file)
                
                #image_location = "\\static\\images\\" + session['username'] + "\\profile\\" + filename
                image_location = "/static/images/" + session['username'] + "/profile/" + filename

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


@app.route('/delete_post/<post_id>', methods=['GET', 'POST'])
def delete_post(post_id):
    post = Post(post_id)
    
    for pic_location in Post(post_id).find()['post_pics']:
        #saved_path = pic_location.split('\\')
        saved_path = pic_location.split('/')
        base = app.config['IMAGE_DELETIONS']
        for subdir in saved_path:
            if subdir != '':
                path = os.path.join(base + '/', subdir)
                updir = base
                base = path

        try:
            os.remove(path)
        except OSError as ex:
            print(ex)
            print("Cannot delete that file.")
        
        try:
            os.rmdir(updir)
        except OSError as ex:
            print(ex)
            print("Directory is not empty.")


    post.delete_comments()
    post.delete_hashtags_only_on_that_post()
    post.delete()
    return redirect(url_for('index'))
    

@app.route('/edit_post/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    p = Post(post_id)
    selected_post = p.find()
    user = p.get_author()
    hashtags = p.get_hashtags()
    comments = p.get_comments()

    if request.method == 'POST':
        header = request.form['header']
        hashtags = request.form['hashtags']
        #body = request.form['body']
        body = request.form.get("body")
        body2 = body.split('\n')
        new_body = ''.join(['<br>' + line for line in body2])
        body = new_body
        radio = request.form['pic_action']
        if radio == 'keep' or radio == 'append':
            post_pics = Post(post_id).find()['post_pics']

        elif radio == 'replace':
            post_pics = []

        if request.files and radio != 'keep':    
            for pic in request.files.getlist("pics"):
                if pic.filename == "":
                    continue
            
                elif allowed_image(pic.filename):
                    filename = secure_filename(pic.filename)
                    short_path = os.path.join(app.config["IMAGE_UPLOADS"] + '/', session['username'])
                    path = os.path.join(short_path + '/', "post")
                    file = os.path.join(path + '/', filename)
                
                    if not os.path.isdir(short_path):
                        os.mkdir(short_path)

                    if not os.path.isdir(path):
                        os.mkdir(path)

                    if not os.path.isfile(file):
                        pic.save(file)
                
                    #pic_location = "\\static\\images\\" + session['username'] + "\\post\\" + filename
                    pic_location = "/static/images/" + session['username'] + "/post/" + filename
                    post_pics.append(pic_location)

                else: 
                    flash("You cannot upload that picture")


        if not header:
            flash('Posting without header is just stupid')
    
        elif not body:
            flash('Posting nothing. How fun')
    
        else:

            if len(post_pics) > 3:
                post_pics = post_pics[-3:]

            Post(post_id).save_edited_post(header, body, post_pics)
            post = Post(post_id)
            old_hashtags = p.get_hashtags()
            post.update_hashtags(old_hashtags, hashtags)
            return open_post(post_id)

    else:
        p = Post(post_id)
        selected_post = p.find()    
        user = p.get_author()
        hashtags = p.get_hashtags()
        comments = p.get_comments()
        return render_template('edit_post.html', post=selected_post, user=user, hashtags=hashtags, comments=comments)



@app.route('/delete_comment/<comment_id>', methods=['GET', 'POST'])
def delete_comment(comment_id):
    comment = Comment(comment_id)
    post_id = comment.get_post_id() 
    comment.delete()
    return open_post(post_id)

@app.route('/edit_comment/<comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    selected_comment = Comment(comment_id).find()
    post_id = Comment(comment_id).get_post_id()
    p = Post(post_id)
    selected_post = p.find()
    user = p.get_author()
    hashtags = p.get_hashtags()
    comments = p.get_comments()
    return render_template(
        'edit_comment.html',
        post=selected_post,
        user=user,
        hashtags=hashtags,
        comments=comments,
        selected_comment=selected_comment     
        )
    

@app.route('/save_edited_comment/<comment_id>', methods=['GET', 'POST'])
def save_comment(comment_id):
    #new_body = request.form['edit_comment']
    body = request.form.get("body")
    body2 = body.split('\n')
    new_body = ''.join(['<br>' + line for line in body2])
    body = new_body
    Comment(comment_id).save_edited_comment(body)
    post_id = Comment(comment_id).get_post_id()
    return open_post(post_id)

if __name__ == "__main__":
    app.secret_key = os.urandom(24)
    app.run(debug=True)
