from flask import render_template, current_app
from flask_mail import Message
from app import mail, db
from threading import Thread
from datetime import datetime

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body, sender=None):
    """Send an email using Flask-Mail"""
    msg = Message(subject, recipients=recipients, sender=sender)
    msg.body = text_body
    msg.html = html_body

    # Send email asynchronously to avoid blocking the main thread
    Thread(
        target=send_async_email,
        args=(current_app._get_current_object(), msg)
    ).start()

def send_password_reset_email(user):
    """Send password reset instructions to a user"""
    # Generate a new reset token
    token = user.generate_reset_token()
    # Save the changes to the database
    db.session.commit()

    # Get sender from app config, fallback to default if not set
    sender = current_app.config.get('MAIL_DEFAULT_SENDER')

    send_email(
        subject='VibeDodo - Reset Your Password',
        recipients=[user.email],
        text_body=render_template('email/reset_password.txt',
                                user=user,
                                token=token,
                                now=datetime.utcnow()),
        html_body=render_template('email/reset_password.html',
                                user=user,
                                token=token,
                                now=datetime.utcnow()),
        sender=sender
    )