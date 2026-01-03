from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
import re


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    next = HiddenField()


class SignUpForm(FlaskForm):
    firstName = StringField('First Name', validators=[
        DataRequired(message="First name is required"),
        Length(min=1, max=100, message="First name must be between 1 and 100 characters")
    ])
    lastName = StringField('Last Name', validators=[
        DataRequired(message="Last name is required"),
        Length(min=1, max=100, message="Last name must be between 1 and 100 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    birthdate = DateField('Date of Birth', validators=[
        DataRequired(message="Date of birth is required")
    ])
    school = StringField('School', validators=[
        DataRequired(message="School is required"),
        Length(min=1, max=250, message="School name is too long")
    ])
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=50, message="Username must be between 3 and 50 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    
    def validate_username(self, field):
        # Only allow alphanumeric and underscores
        if not re.match(r'^[a-zA-Z0-9_]+$', field.data):
            raise ValidationError("Username can only contain letters, numbers, and underscores")
    
    def validate_password(self, field):
        password = field.data
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number")


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    
    def validate_password(self, field):
        password = field.data
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must contain at least one number")


class ProfileForm(FlaskForm):
    firstName = StringField('First Name', validators=[
        DataRequired(message="First name is required"),
        Length(min=1, max=100)
    ])
    lastName = StringField('Last Name', validators=[
        DataRequired(message="Last name is required"),
        Length(min=1, max=100)
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address")
    ])
    birthdate = StringField('Date of Birth', validators=[
        DataRequired(message="Date of birth is required")
    ])
    school = StringField('School', validators=[
        DataRequired(message="School is required"),
        Length(min=1, max=250)
    ])


class AnswerForm(FlaskForm):
    answer = StringField('Answer', validators=[
        DataRequired(message="Please enter your answer")
    ])


class DeleteAccountForm(FlaskForm):
    """Empty form for CSRF protection on account deletion"""
    pass
