from extensions import db
from models import User
admin=User(email='admin@example.com',is_admin=True)
admin.set_password('admin123')
admin.session.add(admin)
db.session.commit()