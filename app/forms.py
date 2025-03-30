from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, ValidationError, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL, Optional
from app.models.user import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    upload_type = RadioField('Upload Type', choices=[('file', 'Upload File'), ('url', 'Import from URL')], default='file')
    image = FileField('Choose Image', validators=[
        Optional(), 
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only!')
    ])
    image_url = StringField('Image URL', validators=[Optional(), URL()])
    caption = TextAreaField('Caption', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Upload')
    
    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False
            
        if self.upload_type.data == 'file' and not self.image.data:
            self.image.errors = list(self.image.errors)
            self.image.errors.append('Please select an image to upload')
            return False
        elif self.upload_type.data == 'url' and not self.image_url.data:
            self.image_url.errors = list(getattr(self.image_url, 'errors', []))
            self.image_url.errors.append('Please provide an image URL')
            return False
            
        return True

class OrderForm(FlaskForm):
    upload_id = HiddenField('Upload ID', validators=[DataRequired()])
    address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    submit = SubmitField('Place Order')
