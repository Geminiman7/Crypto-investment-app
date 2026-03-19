
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, FloatField, FileField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length,EqualTo

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(),EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DepositForm(FlaskForm):
    currency = SelectField('Currency', choices=[('BTC', 'Bitcoin (BTC)'), ('ETH', 'Ethereum (ETH)'), ('USD', 'US Dollar (USD)')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    submit = SubmitField('Deposit')

class WithdrawForm(FlaskForm):
    currency = SelectField('Currency', choices=[('BTC', 'Bitcoin (BTC)'), ('ETH', 'Ethereum (ETH)'), ('USD', 'US Dollar (USD)')], validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    address = StringField('Wallet Address (for crypto)')
    submit = SubmitField('Withdraw')
'''
class OrderForm(FlaskForm):
    pair = SelectField('Trading Pair', choices=[('BTC/USD', 'BTC/USD'), ('ETH/USD', 'ETH/USD')], validators=[DataRequired()])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    price = FloatField('Price (for limit orders)')
    submit = SubmitField('Place Order')
'''
class TicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Submit Ticket')

class OrderForm(FlaskForm):
    pair = SelectField('Trading Pair', choices=[('BTC/USD', 'BTC/USD'), ('ETH/USD', 'ETH/USD')], validators=[DataRequired()])
    type = SelectField('Type', choices=[('buy', 'Buy'), ('sell', 'Sell')], validators=[DataRequired()])
    order_type = SelectField('Order Type', choices=[('market', 'Market'), ('limit', 'Limit')], validators=[DataRequired()])
    quantity = FloatField('Quantity', validators=[DataRequired()])
    price = FloatField('Price (for limit orders)')
    submit = SubmitField('Place Order')
