from hawkg import app
from extensions import db, uploaded_images, mail
from flask import render_template, redirect, flash, url_for, session, request
from flask_security import login_required, roles_required, current_user
from flask_uploads import UploadNotAllowed
from flask_mail import Message
from slugify import slugify
# our objects
from inni.forms import PostForm, ContactForm
from inni.models import Post, Tag
from user.models import User
# our key info
import private

# Displays the home page.
@app.route('/')
@app.route('/index')
@app.route('/index.html')
# Users must be authenticated to view the home page, but they don't have to have any particular role.
# Flask-Security will display a login form if the user isn't already authenticated.
def index():
    posts = Post.query.order_by(Post.publish_date.desc())
    return render_template('inni/index.html', posts=posts)

@app.route('/about')
@app.route('/about/')
@app.route('/about.html')
def about():
    my_variable = "Hey Steve"
    return render_template('inni/about.html', my_variable=my_variable)

@app.route('/contact', methods=('GET', 'POST'))
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # send email
        msg = Message("Message from your visitor" + form.name.data,
                          sender='noreply@flaskinni-dadiletta.c9users.io',
                          recipients=[private.ADMIN_EMAIL])
        msg.body = """
        From: %s <%s>,
        %s
        """ % (form.name.data, form.email.data, form.message.data)
        with app.app_context():
            mail.send(msg)
        flash("Message sent", 'success')
        return redirect(url_for('index'))
    return render_template('inni/contact.html', form=form)

@app.route('/blog')
@app.route('/blog/')
def blog_index():
    posts = Post.query.filter_by(live=True).order_by(Post.publish_date.desc())
    return render_template('inni/blog.html', posts=posts)

@app.route('/blog/new', methods=('GET', 'POST'))
@login_required
@roles_required('admin')
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        image = request.files.get('image')
        filename = None
        try:
            filename = uploaded_images.save(image)
        except:
            flash("The image was not uploaded", 'danger')
        '''
        # tags have been disabled
        if form.new_tag.data:
            new_tag = Tag(form.new_tag.data)
            db.session.add(new_tag)
            db.session.flush()
            tag = new_tag
        else:
            tag = form.tag.data
        '''
        title = form.title.data
        subtitle = form.subtitle.data
        body = form.body.data
        slug = slugify(title)
        post = Post(current_user, title, subtitle, body, slug, image=filename)
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('read', slug=slug))
    return render_template('inni/post.html', form=form, action="new")
    
@app.route('/article/<slug>')
def read(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    return render_template('inni/article.html', post=post)
    
@app.route('/blog/edit/<int:post_id>', methods=('GET', 'POST'))
@roles_required('admin')
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    form = PostForm(obj=post)
    filename = None
    if form.validate_on_submit():
        original_image = post.image
        form.populate_obj(post)
        if form.image.has_file():
            image = request.files.get('image')
            try:
                filename = uploaded_images.save(image)
            except:
                flash("The image was not uploaded")
            if filename:
                post.image = filename
        else:
            post.image = original_image
        '''
        if form.new_tag.data:
            new_tag = Tag(form.new_tag.data)
            db.session.add(new_tag)
            db.session.flush()
            post.tag = new_tag
        '''
        db.session.commit()
        return redirect(url_for('read', slug=post.slug))
    return render_template('inni/post.html', form=form, post=post, action="edit")

@app.route('/blog/delete/<int:post_id>')
@roles_required('admin')
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id).first_or_404()
    post.live = False
    db.session.commit()
    flash("Article deleted", 'success')
    return redirect(url_for('blog_index'))
    
@app.route('/my_account')
@login_required
def my_account():
    return render_template('inni/my_account.html')





