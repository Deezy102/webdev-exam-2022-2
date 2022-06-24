from flask import Blueprint, redirect, render_template, request, flash, url_for
from flask_login import current_user
from sqlalchemy import exc
from app import db, app
from models import Book, Genre, Review, Image
from tools import ImageSaver
import os
bp = Blueprint('books', __name__, url_prefix='/books')

BOOK_PARAMS = ['title','short_desc' ,'year', 'publisher', 'author', 'volume']

def params():
    return {p: request.form.get(p) for p in BOOK_PARAMS }

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
def new():
    return render_template('books/new.html', genres=load_genres(), book={})

@bp.route('/create', methods=["POST"])
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
        flash("Ошибка базы данных при создании страницы книги.", category='danger')
        return redirect(url_for('books.new'))
    flash(f'Книга "{book.title}" была успешно создана.', category='success')
    return redirect(url_for('books.show', book_id = book.id)) 

@bp.route('/show/<int:book_id>')
def show(book_id):
    book = Book.query.get(book_id)
    reviews = Review.query.filter(Review.book_id == book_id).order_by(Review.created_at.desc()).limit(5).all()

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter(Review.book_id == book_id).filter(Review.user_id == current_user.id).first()

    return render_template('books/show.html', book=book, reviews=reviews, user_review=user_review)

@bp.route('/edit/<int:book_id>')
def edit(book_id):
    return render_template('books/edit.html', genres=load_genres(), book=Book.query.get(book_id))

@bp.route('/update/<int:book_id>', methods=["POST"])
def update(book_id):
    try:
        book = Book.query.get(book_id)
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.year = request.form.get('year')
        book.publisher = request.form.get('publisher')
        book.short_desc = request.form.get('short_desc')
        book.volume = request.form.get('volume')
        
        genres_id_list = request.form.getlist('genres')

        for id in genres_id_list:
            genre = Genre.query.get(id)
            book.genres.append(genre)

        db.session.add(book)
        db.session.commit() 
    except:
        flash('Ошибка при обновлении страницы книги', category='danger')
        return redirect(url_for('books.edit', book_id=book.id))
    flash('Книга успешно обновлена', category='success')
    return redirect(url_for('books.show', book_id = book.id))

@bp.route('/delete/<int:book_id>', methods=['GET', 'POST'])
def delete(book_id):
    book = Book.query.get(book_id)
    try:
        db.session.delete(book)
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.image.storage_filename))
        db.session.commit()
    except:
        flash('Ошибка удаления страницы книги', category='danger')
    return redirect(url_for('books.index'))
    
@bp.route('/<int:book_id>/reviews')
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
def create_review(book_id):
    user_id = current_user.id
    review_rating = request.form.get('review-rating')
    review_text = request.form.get('review-text')
    user_review = Review(user_id=user_id, rating=review_rating, text=review_text, book_id=book_id)
    db.session.add(user_review)
    book = Book.query.get(book_id)
    book.rating_sum += int(review_rating)
    book.rating_num += 1
    db.session.commit()
    return redirect(url_for('books.index'))

@bp.route('/popular')
def popular():
    return render_template('books/popular.html') 

