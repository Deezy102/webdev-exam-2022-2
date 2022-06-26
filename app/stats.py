from flask import Blueprint, render_template, request, send_file
from sympy import im
from flask_login import login_required
from auth import check_rights
from app import db
from models import Book, Genre, Review, Visit, User
from sqlalchemy import exc, extract, text
import sqlalchemy as sa
from datetime import timedelta
import datetime
from tools import generate_report

bp = Blueprint('stats', __name__, url_prefix='/stats')

PER_PAGE = 10

@login_required
@check_rights('get_all_stats')
@bp.route('/users')
def users():
    visits = Visit.query.order_by(Visit.created_at.desc())

    page = request.args.get('page', 1, type=int)
    pagination = visits.paginate(page, PER_PAGE)

    visits = pagination.items
    if request.args.get('download_csv'):
        visits = Visit.query.order_by(Visit.created_at.desc()).all()
        records = []
        for i in visits:
            records.append({
                'User': i.user.last_name + ' ' + i.user.first_name + ' ' + (i.user.middle_name or ''), 
                'Book': i.book.title, 
                'Date': i.created_at.strftime("%Y-%m-%d %H:%M:%S")})
        f = generate_report(['User', 'Book', 'Date'], records)
        filename = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S') + 'pages_stat.csv'
        return send_file(f, mimetype='text/csv', as_attachment=True, attachment_filename=filename)

    return render_template('/stats/users.html', visits=visits, pagination=pagination)

@login_required
@check_rights('get_all_stats')
@bp.route('/books')
def books():
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
    if request.args.get('download_csv'):
        records = []
        for i in books:
            records.append({ 
                'Book': i.title, 
                'Views': i.views_stat})
        f = generate_report(['Book', 'Views'] , records)
        filename = datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S') + 'pages_stat.csv'
        return send_file(f, mimetype='text/csv', as_attachment=True, attachment_filename=filename)
    page = request.args.get('page', 1, type=int)
    pagination = books.paginate(page, PER_PAGE)
    
    books = pagination.items

    

    return render_template('/stats/books.html', books=books, pagination=pagination, date_from=date_from, date_to=date_to)