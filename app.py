from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models.Users import User
from models.Users import db
import re

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer,SignatureExpired

from datetime import datetime

# setup the app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = "SuperSecretKey"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

db.init_app(app)
bcrypt = Bcrypt(app)

# Email confirmation
app.config.from_pyfile('config.cfg')
mail = Mail(app)
s = URLSafeTimedSerializer('kalebjordan')


# setup the login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# create the db structure
with app.app_context():
    db.create_all()


####  setup routes  ####
@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)


@app.route("/login", methods=["GET", "POST"])
def login():

    # clear the inital flash message
    session.clear()
    if request.method == 'GET':
        return render_template('login.html')

    # get the form data
    username = request.form['username']
    password = request.form['password']

    remember_me = False
    if 'remember_me' in request.form:
        remember_me = True

    # query the user
    registered_user = User.query.filter_by(username=username).first()

    if registered_user is None:
        flash('Invalid Username/Password')
        return render_template('login.html')

    # check the passwords
    if registered_user and bcrypt.check_password_hash(registered_user.password, password) == False:
        flash('Invalid Username/Password')
        return render_template('login.html')

    # login the user
    login_user(registered_user, remember=remember_me)
    return redirect(request.args.get('next') or url_for('index'))


@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == 'GET':
        session.clear()
        return render_template('register.html')

    # get the data from our form
    password = request.form['password']
    conf_password = request.form['confirm-password']
    username = request.form['username']
    email = request.form['email']

    # hash the password for storage

    n =0
    if conf_password != password:
        flash("Passwords do not match")
        n=4
    if n>0:
        return render_template('register.html')

    # create a user, and check if its unique
    if n==0:
        pw_hash = bcrypt.generate_password_hash(password)
        user = User(username, pw_hash, email)
        u_unique = user.unique()

    # add the user
    if u_unique == 0:
        db.session.add(user)
        db.session.commit()
        flash("Account Created")
        return redirect(url_for('login'))
        
    # else error check what the problem is
    elif u_unique == -1:
        flash("Email address already in use.")
        return render_template('register.html')

    elif u_unique == -2:
        flash("Username already in use.")
        return render_template('register.html')

    else:
        flash("Username and Email already in use.")
        return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/charts')
def charts():
    return render_template('charts.html', user=current_user)


@app.route('/tables')
def tables():
    return render_template('tables.html', user=current_user)


@app.route('/forms')
def forms():
    return render_template('forms.html', user=current_user)


@app.route('/bootstrap-elements')
def bootstrap_elements():
    return render_template('bootstrap-elements.html', user=current_user)


@app.route('/add_church', methods=["GET", "POST"])
def add_church():
    if request.method=='POST':
        church_name = request.form['church_name']
        church_leader = request.form['church_leader']
        church_email = request.form['church_email']
        church_password = request.form['church_password']
        message = '''Hello {} ,
        we hope your the Leader of {} Church
        you have been requested 
        to join Mychurch community here are log in credential 
        \n\n
        Username :{}
        default-password:{}
        \n\n
        Please confirm this email in 24 hours'''.format(church_leader, church_name, church_name, church_password)
        token = s.dumps(church_email, salt='email-confirm')
        link = url_for('confirm', token=token, _external=True)
        msg = Message('Mychurch Email confirm', sender='kalebjordan.kj@gmail.com', recipients=[church_email])
        msg.body= "{}\n\n{}".format(message, link)   
        mail.send(msg) 
        username=church_name
        email=church_email
        pw_hash = bcrypt.generate_password_hash(password=church_password)
        user = User(username, pw_hash, email)
        u_unique = user.unique()

        # add the user
        if u_unique == 0:
            db.session.add(user)
            db.session.commit()
            flash("The Church have been added")
            redirect('/add_church')
        elif u_unique == -1:
            flash("Church Email address exist.")
            redirect('/add_church')

        elif u_unique == -2:
            flash("Church name already exist.")
            redirect('/add_church')

        else:
            flash("Church name and Email already in use.")
            redirect('/add_church')
    return render_template('add_church.html', user=current_user)


@app.route('/confirm-email/<token>')
def confirm(token):
    try:
        church_email = s.loads(token, salt='email-confirm', max_age=3600)
    except SignatureExpired:
        flash('The confirmation link has already expired', 'danger')
        redirect('/')
    user = User.query.filter_by(email =church_email).first_or_404()
    if user.confirmed:
        flash("The email has already confirmed")
        redirect('/')
    else:
        user.confirmed = True
        user.confirmed_on = datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        flash("Thank you you have confirmed your email you can now log in ")
    return render_template('login.html')

def recover(token, methods=['GET', 'POST']):
    if request.method=='GET':
        return




@app.route('/blank-page')
def blank_page():
    return render_template('blank-page.html', user=current_user)


@app.route('/profile')
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/settings')
def settings():
    return render_template('settings.html', user=current_user)

####  end routes  ####


# required function for loading the right user
@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))




if __name__ == "__main__":
	# change to app.run(host="0.0.0.0"), if you want other machines to be able to reach the webserver.
	app.run() 