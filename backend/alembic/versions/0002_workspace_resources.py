"""add workspace projects, tasks, agents, workflows, and knowledge tables"""

from alembic import op

revision = "0002_workspace_resources"
down_revision = "0001_initial_platform"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE IF NOT EXISTS profiles (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
      bio text, timezone varchar(100), preferences jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS projects (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, created_by uuid NOT NULL REFERENCES users(id),
      name varchar(200) NOT NULL, slug varchar(100) NOT NULL, description text, status varchar(30) NOT NULL DEFAULT 'active',
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(), UNIQUE(workspace_id, slug)
    );
    CREATE INDEX IF NOT EXISTS ix_projects_workspace ON projects(workspace_id);
    CREATE TABLE IF NOT EXISTS tasks (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, project_id uuid REFERENCES projects(id) ON DELETE CASCADE,
      assigned_to uuid REFERENCES users(id), created_by uuid NOT NULL REFERENCES users(id), title varchar(300) NOT NULL,
      description text, status varchar(30) NOT NULL DEFAULT 'todo', priority varchar(20) NOT NULL DEFAULT 'medium', due_at timestamptz,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_tasks_workspace ON tasks(workspace_id);
    CREATE TABLE IF NOT EXISTS ai_agents (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, created_by uuid NOT NULL REFERENCES users(id),
      name varchar(200) NOT NULL, description text, provider varchar(100) NOT NULL DEFAULT 'auto', model varchar(200), instructions text,
      status varchar(30) NOT NULL DEFAULT 'active', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS ix_ai_agents_workspace ON ai_agents(workspace_id);
    CREATE TABLE IF NOT EXISTS agent_runs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), agent_id uuid NOT NULL REFERENCES ai_agents(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, status varchar(30) NOT NULL DEFAULT 'queued',
      input jsonb NOT NULL DEFAULT '{}'::jsonb, output jsonb NOT NULL DEFAULT '{}'::jsonb, error text,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS workflows (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, created_by uuid NOT NULL REFERENCES users(id),
      name varchar(200) NOT NULL, definition jsonb NOT NULL DEFAULT '{}'::jsonb, status varchar(30) NOT NULL DEFAULT 'active',
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS workflow_runs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, status varchar(30) NOT NULL DEFAULT 'queued',
      input jsonb NOT NULL DEFAULT '{}'::jsonb, output jsonb NOT NULL DEFAULT '{}'::jsonb,
      created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS knowledge_sources (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, name varchar(300) NOT NULL, source_type varchar(50) NOT NULL,
      source_url varchar(2048), status varchar(30) NOT NULL DEFAULT 'active', created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS documents (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), knowledge_source_id uuid REFERENCES knowledge_sources(id) ON DELETE CASCADE,
      workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE, title varchar(500) NOT NULL, content text,
      metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS embeddings (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), workspace_id uuid NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
      document_id uuid REFERENCES documents(id) ON DELETE CASCADE, model varchar(200) NOT NULL, vector jsonb NOT NULL,
      created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS notifications (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE, title varchar(300) NOT NULL, body text NOT NULL,
      read_at timestamptz, created_at timestamptz NOT NULL DEFAULT now()
    );
    CREATE TABLE IF NOT EXISTS audit_logs (
      id uuid PRIMARY KEY DEFAULT gen_random_uuid(), organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
      workspace_id uuid REFERENCES workspaces(id) ON DELETE CASCADE, user_id uuid REFERENCES users(id), action varchar(200) NOT NULL,
      resource_type varchar(100) NOT NULL, resource_id uuid, metadata jsonb NOT NULL DEFAULT '{}'::jsonb, created_at timestamptz NOT NULL DEFAULT now()
    );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS audit_logs, notifications, embeddings, documents, knowledge_sources, workflow_runs, workflows, agent_runs, ai_agents, tasks, projects, profiles CASCADE")
