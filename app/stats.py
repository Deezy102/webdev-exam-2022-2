from flask import Blueprint, render_template, request
from app import db
from models import Book, Genre, Review, Visit, User
from sqlalchemy import exc, extract, text
import sqlalchemy as sa
from datetime import timedelta
import datetime
bp = Blueprint('stats', __name__, url_prefix='/stats')

PER_PAGE = 10

@bp.route('/users')
def users():
    visits = Visit.query.order_by(Visit.created_at.desc())

    page = request.args.get('page', 1, type=int)
    pagination = visits.paginate(page, PER_PAGE)
    
    visits = pagination.items

    return render_template('/stats/users.html', visits=visits, pagination=pagination)


@bp.route('/books')
def books():
    # date_from = request.args.get('from', datetime.today(), type=datetime) or datetime.today()
    # date_to = request.args.get('to', datetime.today(), type=datetime) or datetime.today()
    # visits = Visit.query.with_entities( 
    #     Visit, 
    #     func.count(Visit.book_id).label('total')
    #     ).
    
    # visits = Book.query.with_entities(
    #     func.count(Book.id).label('total'),
    #     Visit
    # ).join(Visit, Book.id == Visit.book_id ).filter(
    #         extract('day', Visit.created_at) >= datetime.today().day,
    #         extract('month', Visit.created_at) >= datetime.today().month,
    #         extract('year', Visit.created_at) >= datetime.today().year
    #         ).group_by(
    #     Book.id
    # # ).order_by('total')
    # visits = Visit.query.with_entities(
    # ).filter(
    #     Visit.created_at >= date_from
    # ).group_by(
    #     Visit.book_id
    # ).join(Book, Book.id == Visit.book_id).order_by(text('total')).count()
    date_from = request.args.get('from')
    date_to = request.args.get('to')
    if date_from is None or date_from == '':
        # date_from = datetime.datetime.combine(datetime.datetime.now().date(), datetime.time(hour=0, minute=0, second=0)) 
        date_from = datetime.datetime.today() - timedelta(days = 90)
    else:
        date_from = datetime.datetime.strptime(date_from, "%Y-%m-%d") + timedelta(hours=0, minutes=0, seconds=0)
    if date_to is None or date_to == '':
        date_to = datetime.datetime.today()
    else:
        date_to = datetime.datetime.strptime(date_to, "%Y-%m-%d") + timedelta(hours=23, minutes=59, seconds=59)
    
    books = Book.query.order_by(Book.id.asc())
    for book in books:
        book.views_stat = Visit.query.filter(
            Visit.book_id == book.id
        ).filter(
            date_to >= Visit.created_at
        ).filter(
            Visit.created_at >= date_from  
        ).count()
        db.session.add(book)
        db.session.commit()
    books = Book.query.order_by(Book.views_stat.desc())
    page = request.args.get('page', 1, type=int)
    pagination = books.paginate(page, PER_PAGE)
    
    books = pagination.items
    return render_template('/stats/books.html', books=books, pagination=pagination, date_from=date_from, date_to=date_to)