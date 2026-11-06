"""Foundation, immutable history and runtime privileges.

The migration owner needs CREATEROLE on first setup. Runtime login must inherit
reknyx_runtime and must not own tables, migrations, schemas or this function.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("actors", sa.Column("id", sa.String(36), primary_key=True), sa.Column("username", sa.String(100), unique=True, nullable=False), sa.Column("display_name", sa.String(200), nullable=False))
    op.create_table("auth_sessions", sa.Column("token_hash", sa.String(64), primary_key=True), sa.Column("actor_id", sa.String(36), sa.ForeignKey("actors.id"), nullable=False), sa.Column("csrf_token", sa.String(128), nullable=False), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked", sa.Boolean(), nullable=False))
    op.create_index("ix_auth_sessions_actor_id", "auth_sessions", ["actor_id"])
    op.create_table("login_buckets", sa.Column("id", sa.String(64), primary_key=True), sa.Column("window_start", sa.DateTime(timezone=True), nullable=False), sa.Column("attempts", sa.Integer(), nullable=False))
    op.create_table("assessments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("data", JSONB(), nullable=False))
    op.create_index("ix_assessments_created_at", "assessments", ["created_at"])
    op.create_table("assessment_memberships", sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), primary_key=True), sa.Column("actor_id", sa.String(36), sa.ForeignKey("actors.id"), primary_key=True))
    op.create_table("scope_revisions", sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), primary_key=True), sa.Column("version", sa.BigInteger(), primary_key=True), sa.Column("data", JSONB(), nullable=False))
    op.create_table("request_revisions", sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), primary_key=True), sa.Column("revision", sa.BigInteger(), primary_key=True), sa.Column("content", sa.String(4000), nullable=False))
    for name in ("conversation_messages", "audit_events"):
        op.create_table(name, sa.Column("id", sa.String(36), primary_key=True), sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("data", JSONB(), nullable=False))
        op.create_index("ix_" + name + "_assessment_id", name, ["assessment_id"])
        op.create_index("ix_" + name + "_created_at", name, ["created_at"])
    op.create_table("artifacts", sa.Column("id", sa.String(36), primary_key=True), sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id"), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("storage_key", sa.String(32), unique=True, nullable=False), sa.Column("data", JSONB(), nullable=False))
    op.create_index("ix_artifacts_assessment_id", "artifacts", ["assessment_id"])
    op.create_index("ix_artifacts_created_at", "artifacts", ["created_at"])
    op.create_table("idempotency_records", sa.Column("namespace", sa.String(64), primary_key=True), sa.Column("actor_id", sa.String(36), sa.ForeignKey("actors.id"), nullable=False), sa.Column("assessment_id", sa.String(36), sa.ForeignKey("assessments.id")), sa.Column("operation", sa.String(100), nullable=False), sa.Column("resource_path", sa.String(500), nullable=False), sa.Column("key", sa.String(128), nullable=False), sa.Column("digest", sa.String(64), nullable=False), sa.Column("status", sa.Integer(), nullable=False), sa.Column("body", JSONB()), sa.Column("location", sa.String(500)), sa.UniqueConstraint("actor_id", "operation", "resource_path", "key"))
    op.execute("""CREATE FUNCTION reknyx_reject_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
      BEGIN RAISE EXCEPTION 'immutable history cannot be changed' USING ERRCODE = '42501'; END; $$""")
    for name in ("audit_events", "scope_revisions", "request_revisions", "conversation_messages", "artifacts"):
        op.execute(f"CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON {name} FOR EACH ROW EXECUTE FUNCTION reknyx_reject_history_mutation()")
        op.execute(f"CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON {name} FOR EACH STATEMENT EXECUTE FUNCTION reknyx_reject_history_mutation()")
    op.execute("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reknyx_runtime') THEN CREATE ROLE reknyx_runtime NOLOGIN; END IF; END $$")
    op.execute("REVOKE ALL ON FUNCTION reknyx_reject_history_mutation() FROM PUBLIC")
    op.execute("GRANT USAGE ON SCHEMA public TO reknyx_runtime")
    op.execute("GRANT SELECT ON alembic_version TO reknyx_runtime")
    tables = "actors,auth_sessions,login_buckets,assessments,assessment_memberships,scope_revisions,request_revisions,conversation_messages,audit_events,artifacts,idempotency_records"
    op.execute(f"GRANT SELECT,INSERT ON {tables} TO reknyx_runtime")
    op.execute("GRANT UPDATE ON auth_sessions,login_buckets,assessments,idempotency_records TO reknyx_runtime")
    op.execute("REVOKE UPDATE,DELETE,TRUNCATE ON audit_events,scope_revisions,request_revisions,conversation_messages,artifacts FROM reknyx_runtime")


def downgrade():
    # Explicitly destructive; never called by application startup.
    for name in ("idempotency_records", "artifacts", "audit_events", "conversation_messages", "request_revisions", "scope_revisions", "assessment_memberships", "assessments", "login_buckets", "auth_sessions", "actors"):
        op.drop_table(name)
    op.execute("DROP FUNCTION reknyx_reject_history_mutation()")
    # Cluster role is deliberately retained: other isolated databases may use it.
