"""add score model

Revision ID: 0eacb56faaa5
Revises: 221a3050d7b5
Create Date: 2026-06-17 12:50:21.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0eacb56faaa5'
down_revision = '221a3050d7b5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('scores',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('student_name', sa.String(length=120), nullable=False),
    sa.Column('subject', sa.String(length=120), nullable=False),
    sa.Column('score', sa.Float(), nullable=False),
    sa.Column('exam_note', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['name_groups.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('scores')
