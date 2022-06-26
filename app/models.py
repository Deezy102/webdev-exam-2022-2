from flask import url_for
import sqlalchemy as sa
from app import db, app
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from sqlalchemy.dialects.mysql import YEAR
from users_policy import UserPolicy
import os

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(100), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)
    
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    
    created_at = db.Column(db.DateTime, nullable=False, server_default=sa.sql.func.now())
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return app.config.get('ADMIN_ROLE_ID') == self.role_id

    @property
    def is_editor(self):
        return app.config.get('EDITOR_ROLE_ID') == self.role_id

    def can(self, action, record=None):
        users_policy = UserPolicy(record=record)
        method = getattr(users_policy, action, None)
        if method is not None:
            return method()
        return False

    @property
    def full_name(self):
        return ' '.join([self.last_name, self.first_name, self.middle_name or ''])

    def __repr__(self):
        return '<User %r>' % self.login

class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '<Role %r>' % self.name

intermediate_books_genres = db.Table(
    'intermediate_books_genres',
    db.Column('book_id', db.Integer, db.ForeignKey('books.id'), nullable=False),
    db.Column('genre_id', db.Integer, db.ForeignKey('genres.id'), nullable=False)
)

class Book(db.Model):
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    short_desc = db.Column(db.Text, nullable=False)

    year = db.Column(YEAR, nullable=False)
    publisher = db.Column(db.String(100), nullable=False)
    volume = db.Column(db.Integer, nullable=False)
    image_id = db.Column(db.String(100), db.ForeignKey('images.id'))

    rating_num = db.Column(db.Integer, nullable=False, default=0)
    rating_sum = db.Column(db.Integer, nullable=False, default=0)
    views_stat = db.Column(db.Integer)

    genres = db.relationship('Genre', secondary=intermediate_books_genres, lazy='subquery')
    image = db.relationship('Image', cascade="all, delete", uselist=False)

    @property
    def rating(self):
        if self.rating_num > 0:
            return self.rating_sum / self.rating_num
        else:
            return 0
    
    def __repr__(self):
        return '<Book %r>' % self.title

class Genre(db.Model):
    __tablename__ = 'genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=sa.sql.func.now())
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book = db.relationship('Book')
    user = db.relationship('User')

class Image(db.Model):
    __tablename__ = 'images'

    id = db.Column(db.String(100), primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    mime_type = db.Column(db.String(100), nullable=False)
    md5_hash = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=sa.sql.func.now())
    object_id = db.Column(db.Integer)
    object_type = db.Column(db.String(100))

    def __repr__(self):
        return '<Image %r>' % self.file_name

    @property
    def storage_filename(self):
        _, ext = os.path.splitext(self.file_name)
        return self.id + ext

    @property
    def url(self):
        return url_for('image', image_id=self.id)

class Visit(db.Model):
    __tablename__ = 'visit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=sa.sql.func.now())

    user = db.relationship('User')
    book = db.relationship('Book')
    def __repr__(self):
        return '<Visit_log %r>' % self.id