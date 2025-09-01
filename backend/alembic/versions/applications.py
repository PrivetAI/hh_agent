"""Remove LetterGeneration table and update Application

Revision ID: remove_letter_generation
Revises: add_pseudonymization_tables
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'remove_letter_generation'
down_revision = 'add_pseudonymization_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to applications table
    op.add_column('applications', 
        sa.Column('vacancy_title', sa.String(), nullable=True))
    
    op.add_column('applications', 
        sa.Column('status', sa.String(), nullable=False, server_default='pending'))
    
    op.add_column('applications', 
        sa.Column('error_message', sa.Text(), nullable=True))
    
    # Drop letter_generations table
    op.drop_table('letter_generations')
    
    # Create index for status field for faster filtering
    op.create_index('idx_applications_status', 'applications', ['status'])
    
    # Create index for user_id and created_at for history queries
    op.create_index('idx_applications_user_created', 'applications', ['user_id', 'created_at'])


def downgrade() -> None:
    # Remove indexes
    op.drop_index('idx_applications_user_created', table_name='applications')
    op.drop_index('idx_applications_status', table_name='applications')
    
    # Remove new columns from applications
    op.drop_column('applications', 'error_message')
    op.drop_column('applications', 'status')
    op.drop_column('applications', 'vacancy_title')
    
    # Recreate letter_generations table
    op.create_table('letter_generations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('vacancy_id', sa.String(), nullable=False),
        sa.Column('vacancy_title', sa.String(), nullable=False),
        sa.Column('resume_id', sa.String(), nullable=True),
        sa.Column('letter_content', sa.Text(), nullable=False),
        sa.Column('prompt_filename', sa.String(), nullable=True),
        sa.Column('ai_model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )