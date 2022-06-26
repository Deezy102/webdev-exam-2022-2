"""added relationships from logs

Revision ID: 0bd8e7a0fee2
Revises: 5ae81dedb3c0
Create Date: 2022-06-25 14:49:30.025077

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '0bd8e7a0fee2'
down_revision = '5ae81dedb3c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('visit_logs', sa.Column('book_id', sa.Integer(), nullable=False))
    op.drop_index('fk_visit_logs_user_id_users', table_name='visit_logs')
    op.create_foreign_key(op.f('fk_visit_logs_book_id_books'), 'visit_logs', 'books', ['book_id'], ['id'])
    op.create_foreign_key(op.f('fk_visit_logs_user_id_users'), 'visit_logs', 'users', ['user_id'], ['id'])
    op.drop_column('visit_logs', 'path')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('visit_logs', sa.Column('path', mysql.VARCHAR(length=150), nullable=False))
    op.drop_constraint(op.f('fk_visit_logs_user_id_users'), 'visit_logs', type_='foreignkey')
    op.drop_constraint(op.f('fk_visit_logs_book_id_books'), 'visit_logs', type_='foreignkey')
    op.create_index('fk_visit_logs_user_id_users', 'visit_logs', ['user_id'], unique=False)
    op.drop_column('visit_logs', 'book_id')
    # ### end Alembic commands ###