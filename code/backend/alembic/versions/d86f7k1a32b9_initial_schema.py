"""initial_schema

Revision ID: d86f7k1a32b9
Revises: 
Create Date: 2026-04-20 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd86f7k1a32b9'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if sources exists to prevent crashing on schema.sql legacy volumes
    conn = op.get_bind()
    from sqlalchemy import inspect
    inspector = inspect(conn)
    if 'sources' in inspector.get_table_names():
        return

    op.create_table('sources',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('citation_text', sa.Text(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('tags',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tag_name', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('tag_name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('username', sa.String(length=100), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('username')
    )
    op.create_table('objects',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('object_type', sa.String(length=255), nullable=False),
    sa.Column('material', sa.String(length=255), nullable=True),
    sa.Column('findspot', sa.String(length=255), nullable=True),
    sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=True),
    sa.Column('date_discovered', sa.Date(), nullable=True),
    sa.Column('inventory_number', sa.String(length=100), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('date_display', sa.String(length=255), nullable=False),
    sa.Column('date_start', sa.Integer(), nullable=False),
    sa.Column('date_end', sa.Integer(), nullable=False),
    sa.Column('width', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('height', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('depth', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('unit', sa.String(length=20), server_default='cm', nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('inventory_number')
    )
    op.create_index('idx_objects_date_start', 'objects', ['date_start'], unique=False)
    op.create_index('idx_objects_date_end', 'objects', ['date_end'], unique=False)
    op.create_index('idx_objects_type', 'objects', ['object_type'], unique=False)

    op.create_table('images',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('object_id', sa.Integer(), nullable=True),
    sa.Column('source_id', sa.Integer(), nullable=True),
    sa.Column('image_type', sa.String(length=50), nullable=True),
    sa.Column('view_type', sa.String(length=50), nullable=True),
    sa.Column('file_url', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['object_id'], ['objects.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('image_tags',
    sa.Column('image_id', sa.Integer(), nullable=False),
    sa.Column('tag_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['image_id'], ['images.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('image_id', 'tag_id')
    )
    op.create_index('idx_image_tags_tag_id', 'image_tags', ['tag_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_image_tags_tag_id', table_name='image_tags')
    op.drop_table('image_tags')
    op.drop_table('images')
    op.drop_index('idx_objects_type', table_name='objects')
    op.drop_index('idx_objects_date_end', table_name='objects')
    op.drop_index('idx_objects_date_start', table_name='objects')
    op.drop_table('objects')
    op.drop_table('users')
    op.drop_table('tags')
    op.drop_table('sources')
