"""initial multi-tenant platform schema

Revision ID: 0001_initial_platform
"""
from alembic import op

revision = "0001_initial_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("""
    CREATE TABLE users (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), auth_user_id uuid NOT NULL UNIQUE,
      email varchar(320) NOT NULL, display_name varchar(200), avatar_url varchar(2048),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE organizations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), name varchar(200) NOT NULL, slug varchar(100) NOT NULL UNIQUE,
      owner_user_id uuid NOT NULL REFERENCES users(id), created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE organization_members (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE, role varchar(20) NOT NULL CHECK(role IN ('owner','admin','member')),
      created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(organization_id, user_id)
    );
    CREATE TABLE workspaces (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      name varchar(200) NOT NULL, slug varchar(100) NOT NULL, description text, created_by uuid NOT NULL REFERENCES users(id),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(organization_id, slug)
    );
    CREATE TABLE workspace_members (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
      user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE, role varchar(20) NOT NULL DEFAULT 'member',
      created_at timestamptz NOT NULL DEFAULT now(), UNIQUE(workspace_id, user_id)
    );
    CREATE TABLE conversations (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, user_id uuid NOT NULL REFERENCES users(id),
      title varchar(300) NOT NULL DEFAULT 'New conversation', model_provider varchar(100), model_name varchar(200),
      status varchar(20) NOT NULL DEFAULT 'active' CHECK(status IN ('active','archived','deleted')),
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX ix_conversations_org ON conversations(organization_id); CREATE INDEX ix_conversations_workspace ON conversations(workspace_id);
    CREATE INDEX ix_conversations_user ON conversations(user_id); CREATE INDEX ix_conversations_updated ON conversations(updated_at);
    CREATE TABLE messages (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), conversation_id uuid NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
      user_id uuid REFERENCES users(id), role varchar(20) NOT NULL CHECK(role IN ('system','user','assistant','tool')), content text NOT NULL,
      provider varchar(100), model varchar(200), input_tokens integer, output_tokens integer, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now()
    ); CREATE INDEX ix_messages_conversation ON messages(conversation_id); CREATE INDEX ix_messages_created ON messages(created_at);
    CREATE TABLE usage_logs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid REFERENCES workspaces(id), user_id uuid REFERENCES users(id), conversation_id uuid REFERENCES conversations(id),
      provider varchar(100) NOT NULL, model varchar(200) NOT NULL, operation varchar(100) NOT NULL, input_tokens integer,
      output_tokens integer, total_tokens integer, estimated_cost numeric, latency_ms integer, success boolean NOT NULL DEFAULT true,
      error_code varchar(100), metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
    ); CREATE INDEX ix_usage_logs_org ON usage_logs(organization_id);
    CREATE TABLE subscriptions (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      provider varchar(50) NOT NULL DEFAULT 'none', provider_customer_id varchar(255), provider_subscription_id varchar(255),
      plan varchar(100) NOT NULL DEFAULT 'free', status varchar(50) NOT NULL DEFAULT 'active', current_period_start timestamptz,
      current_period_end timestamptz, cancel_at_period_end boolean NOT NULL DEFAULT false, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE files (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, uploaded_by uuid NOT NULL REFERENCES users(id),
      provider varchar(50) NOT NULL, provider_file_id varchar(500), storage_path varchar(1000) NOT NULL, original_name varchar(500) NOT NULL,
      mime_type varchar(200) NOT NULL, size_bytes integer NOT NULL, status varchar(50) NOT NULL DEFAULT 'ready', metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    ); CREATE INDEX ix_files_org ON files(organization_id); CREATE INDEX ix_files_workspace ON files(workspace_id);
    CREATE TABLE document_chunks (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, file_id uuid REFERENCES files(id) ON DELETE CASCADE,
      source_type varchar(100) NOT NULL, source_id varchar(500), content text NOT NULL, embedding vector(1536), metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now()
    ); CREATE INDEX ix_chunks_org_workspace ON document_chunks(organization_id, workspace_id);
    CREATE INDEX ix_chunks_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks, files, subscriptions, usage_logs, messages, conversations, workspace_members, workspaces, organization_members, organizations, users CASCADE")
