from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, RadioField, ValidationError, HiddenField, IntegerField, SelectField, DateField, TimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, URL, Optional, NumberRange, Regexp
from datetime import date, datetime, time
from app.models.user import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    
    # Country selection field - using ISO 3166-1 alpha-2 codes for countries
    country = SelectField('Country', validators=[DataRequired()], choices=[
        ('', 'Select your country'),
        ('US', 'United States'),
        ('GB', 'United Kingdom'),
        ('CA', 'Canada'),
        ('AU', 'Australia'),
        ('DE', 'Germany'),
        ('FR', 'France'),
        ('IN', 'India'),
        ('JP', 'Japan'),
        ('CN', 'China'),
        ('BR', 'Brazil'),
        ('RU', 'Russia'),
        ('ZA', 'South Africa'),
        ('MX', 'Mexico'),
        ('ES', 'Spain'),
        ('IT', 'Italy'),
        ('NL', 'Netherlands'),
        ('SE', 'Sweden'),
        ('NO', 'Norway'),
        ('FI', 'Finland'),
        ('DK', 'Denmark'),
        ('NZ', 'New Zealand'),
        ('SG', 'Singapore'),
        ('AE', 'United Arab Emirates'),
        ('SA', 'Saudi Arabia'),
        ('TR', 'Turkey'),
        ('KR', 'South Korea')
    ])
    
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\s\-\(\)]{8,20}$', message='Please enter a valid phone number.')
    ])
    
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

class TOTPForm(FlaskForm):
    token = StringField('Authentication Code', validators=[
        DataRequired(), 
        Length(min=6, max=6, message="Code must be 6 digits")
    ])
    submit = SubmitField('Verify')

class MFASetupForm(FlaskForm):
    token = StringField('Verification Code', validators=[
        DataRequired(), 
        Length(min=6, max=6, message="Code must be 6 digits")
    ])
    submit = SubmitField('Enable Two-Factor Authentication')

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
    size = RadioField('Postcard Size',
                     choices=[
                         ('small', 'Small (4" x 6") - $5 USD'),
                         ('medium', 'Medium (5" x 7") - $7 USD'),
                         ('large', 'Large (6" x 11") - $10 USD')
                     ],
                     default='small',
                     validators=[DataRequired()])
    quantity = IntegerField('Quantity',
                          validators=[
                              DataRequired(),
                              NumberRange(min=1, max=100, message="Quantity must be between 1 and 100")
                          ],
                          default=1)
    address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    time_slot_id = SelectField('Preferred Delivery Time', coerce=int, validators=[DataRequired()],
                              render_kw={"class": "form-select"})
    unit_price = HiddenField('Unit Price')  # Added hidden field for price (vulnerability)
    submit = SubmitField('Place Order')
    
def validate_card_number(form, field):
    """Custom validator for card number that strips spaces and validates length"""
    if field.data:
        # Remove spaces and non-digit characters
        digits_only = ''.join(filter(str.isdigit, field.data))
        if len(digits_only) != 16:
            raise ValidationError('Card number must be 16 digits')

class PaymentForm(FlaskForm):
    """Form for payment processing"""
    card_number = StringField('Card Number', validators=[
        DataRequired(),
        validate_card_number
    ])
    expiry_month = SelectField('Expiry Month', coerce=int, validators=[DataRequired()],
                              choices=[(i, f"{i:02d}") for i in range(1, 13)])
    expiry_year = SelectField('Expiry Year', coerce=int, validators=[DataRequired()],
                             choices=[(i, str(i)) for i in range(2024, 2035)])
    cvv = StringField('CVV', validators=[
        DataRequired(),
        Length(min=3, max=4, message="CVV must be 3 or 4 digits")
    ])
    submit = SubmitField('Complete Payment')

class TextOverlayForm(FlaskForm):
    """Form for adding text overlay to an image"""
    text = TextAreaField('Text', validators=[Optional(), Length(max=300)])
    x_position = HiddenField('X Position', validators=[Optional()])
    y_position = HiddenField('Y Position', validators=[Optional()])
    font_size = IntegerField('Font Size', validators=[Optional(), NumberRange(min=8, max=72)], default=24)
    color = StringField('Color', validators=[Optional()], default='#000000')
    submit = SubmitField('Save Postcard')
    
    
class DeliveryDayForm(FlaskForm):
    """Form for managing delivery days"""
    date = DateField('Delivery Date', validators=[DataRequired()], format='%Y-%m-%d')
    is_active = BooleanField('Active', default=True)
    max_deliveries = IntegerField('Max Deliveries', validators=[NumberRange(min=1, max=100)], default=20)
    submit = SubmitField('Save Delivery Day')
    
    def validate_date(self, date):
        if date.data < datetime.now().date():
            raise ValidationError('Delivery date cannot be in the past')


class TimeSlotForm(FlaskForm):
    """Form for managing time slots"""
    delivery_day_id = SelectField('Delivery Day', coerce=int, validators=[DataRequired()])
    start_time = TimeField('Start Time', validators=[DataRequired()], format='%H:%M')
    end_time = TimeField('End Time', validators=[DataRequired()], format='%H:%M')
    is_active = BooleanField('Active', default=True)
    max_orders = IntegerField('Max Orders', validators=[NumberRange(min=1, max=50)], default=5)
    submit = SubmitField('Save Time Slot')
    
    def validate_end_time(self, end_time):
        if end_time.data <= self.start_time.data:
            raise ValidationError('End time must be after start time')
            
            
class DeliveryScheduleSelectionForm(FlaskForm):
    """Form for selecting delivery time in the order form"""
    delivery_slot = SelectField('Delivery Time', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Delivery Schedule')
    
class ResetPasswordForm(FlaskForm):
    """Form for admin to reset a user's password"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')

class AdminEditOrderForm(FlaskForm):
    """Form for admin to edit an order"""
    size = RadioField('Postcard Size',
                     choices=[
                         ('small', 'Small (4" x 6") - $5 USD'),
                         ('medium', 'Medium (5" x 7") - $7 USD'),
                         ('large', 'Large (6" x 11") - $10 USD')
                     ],
                     validators=[DataRequired()])
    quantity = IntegerField('Quantity',
                          validators=[
                              DataRequired(),
                              NumberRange(min=1, max=100, message="Quantity must be between 1 and 100")
                          ])
    address = TextAreaField('Delivery Address', validators=[DataRequired(), Length(max=500)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    status = SelectField('Order Status',
                       choices=[
                           ('pending', 'Pending'),
                           ('approved_for_printing', 'Approved for Printing'),
                           ('printed', 'Printed'),
                           ('shipped', 'Shipped'),
                           ('completed', 'Completed'),
                           ('rejected', 'Rejected')
                       ],
                       validators=[DataRequired()])
    print_notes = TextAreaField('Print Notes', validators=[Optional(), Length(max=500)])
    time_slot_id = SelectField('Delivery Time', coerce=int, validators=[Optional()],
                             render_kw={"class": "form-select"})
    submit = SubmitField('Update Order')

class RequestPasswordResetForm(FlaskForm):
    """Form to request password reset"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('There is no account with that email. Please register first.')

class ResetPasswordWithTokenForm(FlaskForm):
    """Form to reset password with a token"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')