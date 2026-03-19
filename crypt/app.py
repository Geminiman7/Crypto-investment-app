# app.py
import os
from flask import Flask, send_file
from extensions import db, login_manager, mail
from flask_login import current_user  # Add for context processor
from flask_uploads import UploadSet, DOCUMENTS, configure_uploads
from flask_migrate import Migrate



# Load environment variables from .env
#load_dotenv()
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)

app.config['UPLOADED_DOCUMENTS_DEST'] = os.path.join(os.getcwd(), 'uploads')
documents = UploadSet('documents', DOCUMENTS)
configure_uploads(app, documents)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
'''
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.example.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'Uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB file size limit

'''
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 8025
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@example.com'
#app.config['ALPACA_API_KEY'] =    'PKJMBGQGFW58CDABRA1I'#os.environ.get('ALPACA_API_KEY', 'your-paper-api-key')
#app.config['ALPACA_SECRET_KEY'] ='DjcqQ3hskHq5AzlWrdZzs9EDkecK84JLie6VTe4k'  #os.environ.get('ALPACA_SECRET_KEY', 'your-paper-secret-key')
#app.config['ALPACA_BASE_URL'] = 'https://paper-api.alpaca.markets'


#Create upload folder if it doesn't exist
#os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
mail.init_app(app)

migrate = Migrate(app, db)

# Define basename filter for templates
#@app.template_filter('basename')
#def basename(path):
   # return os.path.basename(path)

# Ensure current_user is available in all templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Import models, forms, and routes
from models import User, KYCDocument, Transaction, Order, Ticket
from forms import RegistrationForm, LoginForm
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Initialize database tables
    app.run(debug=True)