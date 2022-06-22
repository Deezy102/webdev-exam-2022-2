from flask import Flask, render_template, send_file, abort, send_from_directory, request
from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate



app = Flask(__name__)
application = app

app.config.from_pyfile('config.py')

convention = {
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

PER_PAGE = 3

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(app, metadata=metadata)
migrate = Migrate(app, db)

from models import User, Book, Image
from auth import bp as auth_bp, init_login_manager

app.register_blueprint(auth_bp)

init_login_manager(app)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)

    books = Book.query.order_by(Book.year.desc()).all()
    pagination = books.paginate(page, PER_PAGE)
    books = pagination.items

    return render_template(
        'index.html', 
        books=books,
        pagination=pagination
    )

@app.route('/media/images/<image_id>')
def image(image_id):
    image = Image.query.get(image_id)

    if image is None:
        abort(404)

    return send_from_directory(app.config['UPLOAD_FOLDER'], image.storage_filename)