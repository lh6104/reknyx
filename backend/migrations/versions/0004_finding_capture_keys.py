"""Immutable exact-capture finding identity, without legacy backfill."""
from alembic import op
import sqlalchemy as sa

revision = '0004_finding_capture_keys'
down_revision = '0003_evidence_analysis'
branch_labels = depends_on = None


def upgrade():
    op.create_unique_constraint('uq_findings_assessment_id_id', 'findings', ['assessment_id', 'id'])
    op.create_table('finding_capture_keys',
        sa.Column('assessment_id', sa.String(36), primary_key=True),
        sa.Column('fingerprint', sa.String(64), primary_key=True),
        sa.Column('finding_id', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id', 'finding_id'], ['findings.assessment_id', 'findings.id']))
    op.execute('GRANT SELECT,INSERT ON finding_capture_keys TO reknyx_runtime')
    op.execute('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON finding_capture_keys '
               'FOR EACH ROW EXECUTE FUNCTION reknyx_reject_history_mutation()')
    op.execute('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON finding_capture_keys '
               'FOR EACH STATEMENT EXECUTE FUNCTION reknyx_reject_history_mutation()')


def downgrade():
    op.drop_table('finding_capture_keys')
    op.drop_constraint('uq_findings_assessment_id_id', 'findings', type_='unique')
