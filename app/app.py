from flask import Flask, render_template, send_file, abort, send_from_directory, request
from sqlalchemy import MetaData, extract
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from flask_login import current_user

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

from models import Visit, Book, Image
from auth import bp as auth_bp, init_login_manager
from books import bp as books_bp
from stats import bp as stats_bp

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(stats_bp)

init_login_manager(app)

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)

    books = Book.query.order_by(Book.year.desc())
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

@app.before_request
def log_visit_info():
    if (request.endpoint == 'static' or 
        request.args.get('download_csv') or 
        "media" in request.path):
       return None 
    visit = None
    # запись первых 10 посещений страницы конкретной книги
    if (current_user.is_authenticated and
        Visit.query.filter(
            extract('day', Visit.created_at) >= datetime.today().day,
            extract('month', Visit.created_at) >= datetime.today().month,
            extract('year', Visit.created_at) >= datetime.today().year
            ).filter(
                Visit.user_id == current_user.id
                ).filter(
                    Visit.book_id == request.path[request.path.rfind('/') + 1:]
                    ).count() < 10 and
        'show' in request.path):
        visit = Visit(user_id=current_user.id, book_id=request.path[request.path.rfind('/') + 1:])
    # else:
    #     visit = Visit(user_id = getattr(current_user, 'id', None), path=request.path) 
        try:
            db.session.add(visit)
            db.session.commit()
        except:
            db.session.rollback()   
            print("Ошибка сохранения логов")    
