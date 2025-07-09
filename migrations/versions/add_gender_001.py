"""add gender field

Revision ID: add_gender_001
Revises: 
Create Date: 2025-07-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_gender_001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Cria enum para gender
    op.execute("CREATE TYPE genderenum AS ENUM ('M', 'F', 'O')")
    
    # Adiciona coluna gender
    op.add_column('user_profiles', sa.Column('gender', sa.Enum('M', 'F', 'O', name='genderenum'), nullable=True))

def downgrade():
    # Remove coluna
    op.drop_column('user_profiles', 'gender')
    
    # Remove enum
    op.execute("DROP TYPE genderenum")
