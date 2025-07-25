from flask import Flask, request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, current_user, login_required, LoginManager, UserMixin
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt

import forms

import json
import os
import colorama
from waitress import serve

colorama.init()

with open("config.json", "r", encoding="utf-8") as file:
    config = json.loads(file.read())

SECRET_KEY = os.urandom(32)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = SECRET_KEY

csrf = CSRFProtect(app)
DB = SQLAlchemy(app)
bcrypt = Bcrypt(app)
    
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(DB.Model, UserMixin):
    __tablename__ = "users"
    
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    email = DB.Column(DB.String(120), unique=True, nullable=False)
    password = DB.Column(DB.String(60), nullable=False)
    

class Url(DB.Model):
    __tablename__ = "urls"
    
    id = DB.Column(DB.Integer, primary_key=True, autoincrement=True)
    user_id = DB.Column(DB.Integer, nullable=False)
    name = DB.Column(DB.String(120), unique=True, nullable=False)
    link = DB.Column(DB.String(120), nullable=False)
    views = DB.Column(DB.Integer, nullable=False)


@login_manager.user_loader
def load_user(id):
    return DB.session.get(User, int(id))


@app.route("/", methods=['GET'])
async def index_page():
    return render_template("index.html", siteName=config['siteName'], 
                           developerUrl=config['developerInformation']['developerLolz'],
                           donateUrl=config['developerInformation']['donateUrl']), 200


@app.route("/login", methods=['GET','POST'])
async def login():
    messages = []
    login_form = forms.LoginForm()
    if request.method == "POST":
        if login_form.validate_on_submit():
            user = User.query.filter_by(email=login_form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, login_form.password.data):
                login_user(user, remember=True)
            else:
                messages.append("Enter the correct password or email!")
            
            if not messages:
                if request.args.get("next"):
                    return redirect(str(request.args.get("next"))) 
                else:
                    return redirect("/urls")

    return render_template("login.html", login_form=login_form, siteName=config['siteName'], messages=messages)


@app.route("/register", methods=['GET','POST'])
async def register():
    messages = []
    register_form = forms.RegistrationForm()
    if register_form.validate_on_submit():
        user = User.query.filter_by(email=register_form.email.data).first()
        if user:
            messages.append("There is already a user with this email!")

        if not messages:
            hashed_password = bcrypt.generate_password_hash(register_form.password.data).decode('utf-8')
            user = User(email=register_form.email.data,
                        password=hashed_password)
            DB.session.add(user)
            DB.session.commit()
            user = User.query.filter_by(email=register_form.email.data).first()
            if user and bcrypt.check_password_hash(user.password, register_form.password.data):
                login_user(user, remember=True)
            return redirect("/urls")
    else:
        if register_form.password.data != register_form.confirm_password.data:
            messages.append("Passwords are different!")
    
    return render_template("register.html", register_form=register_form, siteName=config['siteName'], messages=messages)


@app.route("/urls", methods=["GET"])
@login_required
async def urls():
    urls = Url.query.filter_by(user_id=current_user.id).all()
    return render_template("urls.html", siteName=config['siteName'], urls=urls, host=request.host)


@app.route("/urls/create", methods=["GET", "POST"])
@login_required
async def urls_create():
    messages = []
    create_url_form = forms.CreateUrlForm()
    if request.method == "POST":
        if create_url_form.validate_on_submit():
            url = Url.query.filter_by(name=create_url_form.name.data.lower()).first()
            if url:
                messages.append("Enter unique URL name!")
            
            if not messages:
                url = Url(user_id=current_user.id, name=create_url_form.name.data.lower(), 
                          link=create_url_form.link.data, views=0)
                DB.session.add(url)
                DB.session.commit()
                return redirect("/urls")
    
    return render_template("urls_create.html", create_url_form=create_url_form, siteName=config['siteName'], messages=messages)


@app.route("/urls/<int:url_id>/edit", methods=["GET", "POST"])
@login_required
async def urls_edit(url_id):
    messages = []
    url = DB.session.get(Url, url_id)
    edit_url_form = forms.EditUrlForm()
    if url:
        if request.method == "POST":
            if edit_url_form.validate_on_submit():
                updates = {}
                
                if edit_url_form.name.data.lower() != url.name:
                    current_url = Url.query.filter_by(name=edit_url_form.name.data.lower()).first()
                    if current_url:
                        messages.append("Enter unique URL name!")
                    else:
                        updates["name"] = edit_url_form.name.data.lower()
                if edit_url_form.link.data != url.link:
                    updates["link"] = edit_url_form.link.data
                
                if not messages:
                    if updates:
                        DB.session.query(Url).filter_by(id=url_id).update(updates)
                        DB.session.commit()
                    return redirect("/urls")
        
        return render_template("urls_edit.html", edit_url_form=edit_url_form, siteName=config['siteName'], messages=messages, url=url)
    else:
        return redirect("/urls")


@app.route("/urls/<int:url_id>/delete", methods=["GET", "POST"])
@login_required
async def urls_delete(url_id):
    url = DB.session.get(Url, url_id)
    delete_form = forms.DeleteUrlForm()
    if url:
        if request.method == "POST":
            if delete_form.validate_on_submit():
                DB.session.query(Url).filter_by(id=url_id).delete()
                DB.session.commit()
                return redirect("/urls")
                
        return render_template("urls_delete.html", delete_url_form=delete_form, siteName=config['siteName'], url=url, host=request.host)
    else:
        return redirect("/urls")


@app.route('/<path:url_name>', methods=['GET'])
async def custom_url(url_name):
    url = Url.query.filter_by(name=url_name).first_or_404()
    url.views += 1
    DB.session.commit()
    return redirect(url.link)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', siteName=config['siteName']), 404


with app.app_context():
    DB.create_all()

if __name__ == "__main__":
    print(colorama.Fore.GREEN + "=====================================")
    print(colorama.Fore.RED + f"{config['siteName']} Was Started")
    print(colorama.Fore.LIGHTBLUE_EX + "Developer: https://t.me/ToSa_LZT")
    print(colorama.Fore.LIGHTBLUE_EX + "TG Channel: https://t.me/ToSa_GG")
    print(colorama.Fore.GREEN + "=====================================" + colorama.Fore.RESET)
    serve(app, host="0.0.0.0", port=config['sitePort'])