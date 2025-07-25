from flask_wtf import FlaskForm

from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, Length, URL

from app import config


class RegistrationForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message="Enter the correct email!")])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    

class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(), Email(message="Enter the correct email!")])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')
    

class CreateUrlForm(FlaskForm):
    name = StringField('URL Name', validators=[DataRequired(), Length(config['minUrlLength'], config['maxUrlLength'])])
    link = StringField("URL Link", validators=[DataRequired(), URL(message="Enter link!")])
    submit = SubmitField('Create URL')
    
    
class EditUrlForm(FlaskForm):
    name = StringField('URL Name', validators=[DataRequired(), Length(config['minUrlLength'], config['maxUrlLength'])])
    link = StringField("URL Link", validators=[DataRequired(), URL(message="Enter link!")])
    submit = SubmitField('Save')
    

class DeleteUrlForm(FlaskForm):
    submit = SubmitField('Delete URL')