# app/__init__.py
from flask import Flask
from .extensions import db, admin
from flask_migrate import Migrate
from .models import User, Attendance, KnownFace
from flask_admin.contrib.sqla import ModelView

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SECRET_KEY'] = 'a5d1c3b6742e48a9d4b2d7f6e3f0a91258b5c8e4'

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    admin.init_app(app)

    # Register models with Flask-Admin
    admin.add_view(ModelView(User, db.session))
    admin.add_view(ModelView(Attendance, db.session))
    admin.add_view(ModelView(KnownFace, db.session))

    # Function to load known faces from the database
    def load_known_faces_and_names_from_db():
        global known_faces, known_names
        known_faces = []
        known_names = []

        # Explicitly using the app context to interact with the database
        with app.app_context():  # Pushing the app context
            known_faces_data = KnownFace.query.all()  # Query the database
            for face in known_faces_data:
                known_faces.append(face.encoding)
                known_names.append(face.name)

    # Call the function to load faces on app initialization
    load_known_faces_and_names_from_db()

    # Import and register blueprints or routes
    from .routes import app as routes_blueprint
    app.register_blueprint(routes_blueprint)

    return app

