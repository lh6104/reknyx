"""Durable analysis reservations and immutable completed decisions."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
revision='0003_evidence_analysis'
down_revision='0002_import_reporting'
branch_labels=depends_on=None

def upgrade():
    for table in ('analysis_attempts','analysis_decisions'):
        op.create_table(table,sa.Column('id',sa.String(36),primary_key=True),
          sa.Column('assessment_id',sa.String(36),sa.ForeignKey('assessments.id'),nullable=False),
          sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('data',JSONB(),nullable=False))
        for field in ('assessment_id','created_at'):op.create_index(f'ix_{table}_{field}',table,[field])
        op.execute(f'GRANT SELECT,INSERT ON {table} TO reknyx_runtime')
    op.execute('GRANT UPDATE ON analysis_attempts TO reknyx_runtime')
    for operation in ('UPDATE OR DELETE','TRUNCATE'):
        trigger='immutable_rows' if operation!='TRUNCATE' else 'immutable_truncate'
        granularity='ROW' if operation!='TRUNCATE' else 'STATEMENT'
        op.execute(f'CREATE TRIGGER {trigger} BEFORE {operation} ON analysis_decisions FOR EACH {granularity} EXECUTE FUNCTION reknyx_reject_history_mutation()')

def downgrade():
    op.drop_table('analysis_decisions')
    op.drop_table('analysis_attempts')
