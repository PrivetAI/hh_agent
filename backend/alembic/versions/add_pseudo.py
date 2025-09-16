# """Add pseudonymization tables

# Revision ID: add_pseudonymization_tables
# Revises: [previous_revision_id]
# Create Date: 2025-07-15 10:00:00.000000

# """
# from alembic import op
# import sqlalchemy as sa
# from sqlalchemy.dialects import postgresql

# # revision identifiers, used by Alembic.
# revision = 'add_pseudonymization_tables'
# down_revision = None  # Замените на ID предыдущей миграции
# branch_labels = None
# depends_on = None


# def upgrade() -> None:
#     # Создаем схему pseudonymization
#     op.execute('CREATE SCHEMA IF NOT EXISTS pseudonymization')
    
#     # Создаем таблицу mapping_sessions
#     op.create_table(
#         'mapping_sessions',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, 
#                  server_default=sa.text('uuid_generate_v4()')),
#         sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('created_at', sa.DateTime(), nullable=True, 
#                  server_default=sa.text('now()')),
#         sa.Column('expires_at', sa.DateTime(), nullable=True, 
#                  server_default=sa.text("now() + interval '7 days'")),
#         sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
#         sa.PrimaryKeyConstraint('id'),
#         schema='pseudonymization'
#     )
    
#     # Создаем таблицу mappings
#     op.create_table(
#         'mappings',
#         sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, 
#                  server_default=sa.text('uuid_generate_v4()')),
#         sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
#         sa.Column('original_value', sa.Text(), nullable=False),
#         sa.Column('pseudonym', sa.Text(), nullable=False),
#         sa.Column('data_type', sa.String(length=50), nullable=False),
#         sa.Column('created_at', sa.DateTime(), nullable=True, 
#                  server_default=sa.text('now()')),
#         sa.ForeignKeyConstraint(['session_id'], ['pseudonymization.mapping_sessions.id'], 
#                                ondelete='CASCADE'),
#         sa.PrimaryKeyConstraint('id'),
#         schema='pseudonymization'
#     )
    
#     # Создаем индексы для быстрого поиска
#     op.create_index('idx_mappings_session', 'mappings', ['session_id'], 
#                    unique=False, schema='pseudonymization')
#     op.create_index('idx_mappings_pseudonym', 'mappings', ['session_id', 'pseudonym'], 
#                    unique=False, schema='pseudonymization')
    
#     # Создаем индекс для очистки истекших сессий
#     op.create_index('idx_mapping_sessions_expires', 'mapping_sessions', ['expires_at'], 
#                    unique=False, schema='pseudonymization')


# def downgrade() -> None:
#     # Удаляем индексы
#     op.drop_index('idx_mapping_sessions_expires', table_name='mapping_sessions', 
#                  schema='pseudonymization')
#     op.drop_index('idx_mappings_pseudonym', table_name='mappings', 
#                  schema='pseudonymization')
#     op.drop_index('idx_mappings_session', table_name='mappings', 
#                  schema='pseudonymization')
    
#     # Удаляем таблицы
#     op.drop_table('mappings', schema='pseudonymization')
#     op.drop_table('mapping_sessions', schema='pseudonymization')
    
#     # Удаляем схему (только если она пустая)
#     op.execute('DROP SCHEMA IF EXISTS pseudonymization CASCADE')