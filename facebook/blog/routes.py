from flask import render_template,redirect,flash,url_for,request,Response
from blog import app,db,bcrypt,photos
from PIL import Image
import secrets,os
from blog.forms import RegistrationForm,LoginForm,UpdateAccountForm,PostForm
from blog.models import User,Post
from flask_login import login_user,logout_user,current_user,login_required
from flask_admin import BaseView, expose

@app.route('/')
def home():
    page=request.args.get('page',1,type=int)
    posts=Post.query.order_by(Post.date.desc()).paginate(page=page,per_page=5)
    return render_template('home.html',title='Home',posts=posts)



@app.route('/about')
def about():
    return render_template('about.html',title='About')

@app.route('/register',methods=['GET','POST'])

def register():

    form=RegistrationForm()
    if form.validate_on_submit():
        hashed=bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user=User(username=form.username.data,email=form.email.data,password=hashed)
        db.session.add(user)
        db.session.commit()
        flash(f'Account Created Successfully','success')
        return redirect(url_for('login'))
    return render_template('register.html',title='Register',form=form)


@app.route('/login',methods=['GET','POST'])
def login():
    form=LoginForm()
    if form.validate_on_submit():
        user=User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user)
            return redirect(url_for('home'))
            flash(f'Welcome You Successfully loged in','success')
        else:
            flash(f'Login Unsuccessfull Try again','danger')
    return render_template('login.html',form=form,title='Login')

@app.route('/logout')

def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    return render_template('profile.html')

def save_photo(picture):
    random=secrets.token_hex(8)
    _,ext=os.path.splitext(picture.filename)
    name=random+ext
    Path=os.path.join(app.root_path,'static/profile',name)
    output=(125,125)
    i=Image.open(picture)
    i.thumbnail(output)
    i.save(Path)
    return name

@app.route('/account',methods=['GET','POST'])

@login_required
def account():
    form=UpdateAccountForm()
    if form.validate_on_submit():
        if form.image.data:
            photo=save_photo(form.image.data)
            current_user.image=photo
        current_user.username=form.username.data
        current_user.email=form.email.data
        db.session.commit()
        flash('Successfully Updated','success')
        return redirect(url_for('account'))
    elif request.method=='GET':
        form.username.data=current_user.username
        form.email.data=current_user.email
    image=url_for('static',filename='profile/'+current_user.image)
    return render_template('account.html',title='Account',image=image,form=form)


@app.route('/post/new',methods=['GET','POST'])
@login_required

def new_post():
    form=PostForm()
    if form.validate_on_submit():
        title=form.title.data
        content=form.content.data
        image1=photos.save(request.files.get('image1'),name=secrets.token_hex(10)+".")
        post=Post(title=title,content=content,image1=image1,author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your Post Created Succefully','success')
        return redirect(url_for('home'))
    return render_template('CreatePost.html',title='New Post',form=form)


@app.route('/post/<int:post_id>',methods=['GET','POST'])
def post(post_id):
    post=Post.query.get_or_404(post_id)    
    return render_template('post.html',title=post.title,post=post)


@app.route("/post/<int:post_id>/+",methods=['GET','POST'])
@login_required
def edit_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author!=current_user:
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.title=form.title.data
        post.content=form.content.data
        db.session.commit()
        flash('Post Has Been Edited','success')
        return redirect(url_for('post',post_id=post.id))
    elif request.method=='GET':
        form.title.data=post.title
        form.content.data=post.content
    return render_template('CreatePost.html',title='Update Post',form=form)



@app.route('/post/<int:post_id>/delete',methods=['GET','POST'])
@login_required

def delete_post(post_id):
    post=Post.query.get_or_404(post_id)
    if post.author!=current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Post Successfully Deleted','success')
    return redirect(url_for('home'))

