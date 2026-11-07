"""Durable imports, immutable observations, attributed reviews and report snapshots."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0002_import_reporting'
down_revision = '0001_foundation'
branch_labels = depends_on = None
TABLES = ('imports', 'observations', 'findings', 'finding_reviews', 'reports', 'report_snapshots')
IMMUTABLE = ('observations', 'finding_reviews', 'report_snapshots')

def upgrade():
    for name in TABLES:
        columns = [sa.Column('id', sa.String(36), primary_key=True),
                   sa.Column('assessment_id', sa.String(36), sa.ForeignKey('assessments.id'), nullable=False),
                   sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
                   sa.Column('data', JSONB(), nullable=False)]
        if name == 'observations':
            columns.append(sa.Column('source_data', JSONB(), nullable=False))
        if name == 'imports':
            columns.append(sa.Column('source_label', sa.String(200), nullable=False))
        op.create_table(name, *columns)
        for field in ('assessment_id', 'created_at'):
            op.create_index(f'ix_{name}_{field}', name, [field])
        op.execute(f'GRANT SELECT,INSERT ON {name} TO reknyx_runtime')
        if name not in IMMUTABLE:
            op.execute(f'GRANT UPDATE ON {name} TO reknyx_runtime')
        else:
            op.execute(f'CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION reknyx_reject_history_mutation()')
            op.execute(f'CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON {name} FOR EACH STATEMENT EXECUTE FUNCTION reknyx_reject_history_mutation()')

def downgrade():
    for name in reversed(TABLES):
        op.drop_table(name)
