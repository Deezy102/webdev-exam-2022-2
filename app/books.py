from datetime import datetime, timedelta
from flask import Blueprint, make_response, redirect, render_template, request, flash, url_for
from flask_login import current_user, login_required
from sqlalchemy import exc, extract, func
from auth import check_rights
from app import db, app
from models import Book, Genre, Review, Visit
from tools import ImageSaver
import os
import bleach
import markdown

bp = Blueprint('books', __name__, url_prefix='/books')

BOOK_PARAMS = ['title','short_desc' ,'year', 'publisher', 'author', 'volume']

def params():
    return {p: bleach.clean(request.form.get(p)) for p in BOOK_PARAMS }

def load_genres():
    genres = Genre.query.all()
    return genres

PER_PAGE = 3

@bp.route('/')
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

@bp.route('/new')
@login_required
@check_rights('create')
def new():
    return render_template('books/new.html', genres=load_genres(), book={})

@bp.route('/create', methods=["POST"])
@login_required
@check_rights('create')
def create():
    
    book = Book(**params())
    genres_id_list = request.form.getlist('genres')
    
    f = request.files.get('background_img') or None
    img = None
    if f and f.filename:
        img = ImageSaver(f).save()
        book.image = img
    else:
        flash("Ошибка создания страницы книги. Добавьте обложку", category='danger')
        return redirect(url_for('books.new'))
    
    try:
        for id in genres_id_list:
            genre = Genre.query.get(id)
            book.genres.append(genre)        
        db.session.add(book)
        db.session.commit()
        print('CREATION!!!!!!!!!!!!!!!')
    except exc.SQLAlchemyError:
        db.session.rollback()
        flash("Ошибка базы данных при создании страницы книги.", category='danger')
        return redirect(url_for('books.new'))
    flash(f'Книга "{book.title}" была успешно создана.', category='success')
    return redirect(url_for('books.show', book_id = book.id)) 

@bp.route('/show/<int:book_id>')
def show(book_id):
    book = Book.query.get(book_id)
    reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.created_at.desc()).limit(5).all()
    book_desc = markdown.markdown(book.short_desc)

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter(Review.book_id == book_id).filter(Review.user_id == current_user.id).first()

    resp = make_response(render_template('books/show.html', book=book, book_desc=book_desc, reviews=reviews, user_review=user_review))
    cookie = request.cookies.get('Recent Books') or ''
    
    if cookie.count('>') == 5 and f"<{book_id}>" not in cookie:
        cookie = cookie[cookie.find('>') + 1:] + f'<{book_id}>'
    if cookie.count('>') < 5 and f"<{book_id}>" not in cookie:
        cookie += f'<{book_id}>'

    resp.set_cookie('Recent Books', cookie)
    return resp

@bp.route('/recent')
@login_required
def recent():
    cookie = request.cookies.get('Recent Books')
    book_ids = []
    k = 0
    for i in cookie:
        if i == '<':
            book_ids.append('')
        if i.isdigit():
            book_ids[k] += i
        if i == '>':
            k += 1
    books = []
    for book_id in book_ids:
        book = Book.query.get(book_id)
        books.append(book)
    books.reverse()
    return render_template('books/recent.html', books=books)

@bp.route('/edit/<int:book_id>')
@login_required
@check_rights('update')
def edit(book_id):
    return render_template('books/edit.html', genres=load_genres(), book=Book.query.get(book_id))

@bp.route('/update/<int:book_id>', methods=["POST"])
@login_required
@check_rights('update')
def update(book_id):
    try:
        book = Book.query.get(book_id)
        book.title = bleach.clean(request.form.get('title'))
        book.author = bleach.clean(request.form.get('author'))
        book.year = bleach.clean(request.form.get('year'))
        book.publisher = bleach.clean(request.form.get('publisher'))
        book.short_desc = bleach.clean(request.form.get('short_desc'))
        book.volume = bleach.clean(request.form.get('volume'))
        
        genres_id_list = request.form.getlist('genres')

        for id in genres_id_list:
            genre = Genre.query.get(id)
            book.genres.append(genre)

        db.session.add(book)
        db.session.commit() 
    except:
        db.session.rollback()
        flash('Ошибка при обновлении страницы книги', category='danger')
        return redirect(url_for('books.edit', book_id=book.id))
    flash('Книга успешно обновлена', category='success')
    return redirect(url_for('books.show', book_id = book.id))

@bp.route('/delete/<int:book_id>', methods=['GET', 'POST'])
@login_required
@check_rights('delete')
def delete(book_id):
    book = Book.query.get(book_id)
    try:
        reviews = Review.query.filter(Review.book_id == book_id).all()
        for review in reviews:
            db.session.delete(review)

        visits = Visit.query.filter(Visit.book_id == book_id).all()
        for visit in visits:
            db.session.delete(visit)
        
        db.session.delete(book)
        db.session.commit()
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.image.storage_filename))
    except:
        db.session.rollback()
        flash('Ошибка удаления страницы книги', category='danger')
    return redirect(url_for('books.index'))
    
@bp.route('/<int:book_id>/reviews')
@login_required    
def reviews(book_id):
    page = request.args.get('page', 1, type=int)
    sort_type = request.args.get('filters')
    reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.created_at.desc())

    if sort_type == 'new': reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.created_at.desc())
    if sort_type == 'old': reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.created_at.asc())
    if sort_type == 'positive': reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.rating.desc())
    if sort_type == 'negative': reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.rating.asc())

    pagination = reviews.paginate(page, PER_PAGE)
    reviews = reviews.paginate(page, PER_PAGE).items

    return render_template('books/reviews.html', reviews=reviews, pagination=pagination)

@bp.route('/<int:book_id>/reviews/create', methods=["POST"])
@login_required 
def create_review(book_id):
    user_id = current_user.id
    review_rating = request.form.get('review-rating')
    review_text = bleach.clean(request.form.get('review-text'))
    user_review = Review(user_id=user_id, rating=review_rating, text=review_text, book_id=book_id)
    db.session.add(user_review)
    book = Book.query.get(book_id)
    book.rating_sum += int(review_rating)
    book.rating_num += 1
    db.session.commit()
    return redirect(url_for('books.index'))

@bp.route('/popular')
def popular():
    pop_books_ids = Book.query.with_entities(Visit.book_id, func.count(Visit.book_id).label('total')).filter(
        datetime.today() >= datetime.today() - timedelta(days = 90) 
        ).group_by(Visit.book_id).order_by('total').all()
    # сортировка списка кортежей по убыванию второго элемента, так как desc в запросе выдавал ошибку
    pop_books_ids.sort(key=lambda i:i[1], reverse=True)
    pop_books = []
    views_books = []
    for i in pop_books_ids:
        if Book.query.get(i[0]) is not None and len(pop_books) < 5:
            pop_books.append(Book.query.get(i[0]))
            views_books.append(i[1])
    print(pop_books)
    return render_template('books/popular.html', books=pop_books, views=views_books) 



