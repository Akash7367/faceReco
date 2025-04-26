from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

# Initialize extensions
db = SQLAlchemy()
admin = Admin(name='Admin Panel', template_mode='bootstrap4')
admin = Admin(name='My Admin Panel', template_mode='bootstrap4', url='/new_add2')
