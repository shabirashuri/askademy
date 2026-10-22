"""Create the complete Smart Item Bank PostgreSQL schema.

Revision ID: 0002_complete_item_bank_schema
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002_complete_item_bank_schema"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EMBEDDING_DIMENSIONS = 1536

user_role = postgresql.ENUM("admin", "teacher", "student", name="user_role", create_type=False)
question_type = postgresql.ENUM("mcq", "short_answer", name="question_type", create_type=False)
question_source = postgresql.ENUM("ai", "manual", name="question_source", create_type=False)
question_status = postgresql.ENUM(
    "draft", "approved", "rejected", "archived", name="question_status", create_type=False
)
difficulty = postgresql.ENUM("easy", "medium", "hard", name="difficulty", create_type=False)
material_status = postgresql.ENUM(
    "uploaded", "extracting", "ready", "failed", name="material_status", create_type=False
)
run_status = postgresql.ENUM(
    "queued",
    "running",
    "awaiting_review",
    "completed",
    "failed",
    name="run_status",
    create_type=False,
)
assessment_status = postgresql.ENUM(
    "draft", "published", "closed", name="assessment_status", create_type=False
)
attempt_status = postgresql.ENUM(
    "in_progress", "submitted", "graded", name="attempt_status", create_type=False
)
action_status = postgresql.ENUM(
    "open", "done", "dismissed", name="action_status", create_type=False
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    for enum_type in (
        user_role,
        question_type,
        question_source,
        question_status,
        difficulty,
        material_status,
        run_status,
        assessment_status,
        attempt_status,
        action_status,
    ):
        enum_type.create(bind, checkfirst=True)

    op.add_column("users", sa.Column("full_name", sa.String(255), nullable=True))
    op.execute("UPDATE users SET full_name = email WHERE full_name IS NULL")
    op.alter_column("users", "full_name", nullable=False)
    op.add_column(
        "users",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.alter_column("users", "email", type_=postgresql.CITEXT(), postgresql_using="email::citext")
    op.alter_column("users", "role", type_=user_role, postgresql_using="role::user_role")

    op.alter_column("courses", "name", new_column_name="title")
    op.alter_column("courses", "owner_id", new_column_name="teacher_id")
    op.drop_index("ix_courses_owner_id", table_name="courses")
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])
    op.add_column("courses", sa.Column("code", sa.String(50), nullable=True))
    op.execute("UPDATE courses SET code = 'COURSE-' || left(id::text, 8) WHERE code IS NULL")
    op.alter_column("courses", "code", nullable=False)
    op.create_unique_constraint("uq_courses_code", "courses", ["code"])
    op.add_column(
        "courses",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column("courses", sa.Column("deleted_at", sa.DateTime(timezone=True)))

    op.alter_column("topics", "name", new_column_name="title")
    op.drop_constraint("uq_topics_course_name", "topics", type_="unique")
    op.add_column("topics", sa.Column("parent_topic_id", sa.Uuid(), nullable=True))
    op.add_column("topics", sa.Column("position", sa.Integer(), server_default="0", nullable=False))
    op.add_column(
        "topics",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.add_column("topics", sa.Column("deleted_at", sa.DateTime(timezone=True)))
    op.create_foreign_key(
        "fk_topics_parent_topic_id",
        "topics",
        "topics",
        ["parent_topic_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_topics_course_title_parent", "topics", ["course_id", "title", "parent_topic_id"]
    )

    op.create_table(
        "course_enrollments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("course_id", "student_id"),
    )
    op.create_table(
        "materials",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "uploaded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("content_hash", sa.String(128), nullable=False),
        sa.Column("status", material_status, nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("extracted_text", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("file_type IN ('pdf', 'pptx', 'docx')", name="ck_materials_file_type"),
    )
    op.create_index("ix_materials_course_id", "materials", ["course_id"])
    op.create_index("ix_materials_topic_id", "materials", ["topic_id"])
    op.create_index("ix_materials_content_hash", "materials", ["content_hash"])
    op.create_table(
        "material_chunks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "material_id",
            sa.Uuid(),
            sa.ForeignKey("materials.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_or_slide", sa.Integer()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIMENSIONS)),
        sa.UniqueConstraint("material_id", "chunk_index"),
    )
    op.create_index("ix_material_chunks_course_topic", "material_chunks", ["course_id", "topic_id"])
    op.create_index(
        "ix_material_chunks_embedding_hnsw",
        "material_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_table(
        "generation_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "requested_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("material_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column(
            "settings", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.Column("langgraph_thread_id", sa.Text(), nullable=False, unique=True),
        sa.Column("status", run_status, nullable=False),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer()),
        sa.Column("output_tokens", sa.Integer()),
        sa.Column("estimated_cost", sa.Numeric(10, 4)),
        sa.Column("error_message", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column(
            "created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("source", question_source, nullable=False),
        sa.Column(
            "generation_run_id", sa.Uuid(), sa.ForeignKey("generation_runs.id", ondelete="SET NULL")
        ),
        sa.Column(
            "source_chunk_id", sa.Uuid(), sa.ForeignKey("material_chunks.id", ondelete="SET NULL")
        ),
        sa.Column("type", question_type, nullable=False),
        sa.Column("stem", sa.Text(), nullable=False),
        sa.Column("correct_answer_text", sa.Text()),
        sa.Column("explanation", sa.Text()),
        sa.Column("difficulty", difficulty),
        sa.Column("marks", sa.Numeric(5, 2), server_default="1", nullable=False),
        sa.Column("status", question_status, server_default="draft", nullable=False),
        sa.Column("times_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column("search_vector", postgresql.TSVECTOR()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index(
        "ix_questions_course_topic_status", "questions", ["course_id", "topic_id", "status"]
    )
    op.create_index(
        "ix_questions_search_vector", "questions", ["search_vector"], postgresql_using="gin"
    )
    op.create_table(
        "question_options",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(1), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.UniqueConstraint("question_id", "label"),
        sa.UniqueConstraint("question_id", "position"),
    )
    op.create_index(
        "uq_question_options_one_correct",
        "question_options",
        ["question_id"],
        unique=True,
        postgresql_where=sa.text("is_correct"),
    )
    op.create_table(
        "tags",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.UniqueConstraint("course_id", "name"),
    )
    op.create_table(
        "question_tags",
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("questions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id", sa.Uuid(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
        ),
    )
    op.create_table(
        "assessments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("instructions", sa.Text()),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("duration_minutes", sa.Integer()),
        sa.Column("available_from", sa.DateTime(timezone=True)),
        sa.Column("available_until", sa.DateTime(timezone=True)),
        sa.Column("max_attempts", sa.Integer(), server_default="1", nullable=False),
        sa.Column(
            "shuffle_questions", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("status", assessment_status, server_default="draft", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "assessment_questions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("marks", sa.Numeric(5, 2)),
        sa.UniqueConstraint("assessment_id", "question_id"),
        sa.UniqueConstraint("assessment_id", "position"),
    )
    op.create_table(
        "attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Uuid(),
            sa.ForeignKey("assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", attempt_status, server_default="in_progress", nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True)),
        sa.Column("score", sa.Numeric(6, 2)),
        sa.Column("max_score", sa.Numeric(6, 2), nullable=False),
        sa.UniqueConstraint("assessment_id", "student_id", "attempt_number"),
    )
    op.create_table(
        "attempt_answers",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "attempt_id",
            sa.Uuid(),
            sa.ForeignKey("attempts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "question_id",
            sa.Uuid(),
            sa.ForeignKey("questions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "selected_option_id",
            sa.Uuid(),
            sa.ForeignKey("question_options.id", ondelete="SET NULL"),
        ),
        sa.Column("answer_text", sa.Text()),
        sa.Column("is_correct", sa.Boolean()),
        sa.Column("awarded_marks", sa.Numeric(5, 2)),
        sa.Column("ai_feedback", sa.Text()),
        sa.Column("graded_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.UniqueConstraint("attempt_id", "question_id"),
    )
    op.create_table(
        "exports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "requested_by",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("question_ids", postgresql.ARRAY(sa.Uuid()), nullable=False),
        sa.Column(
            "include_answer_key", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("storage_path", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_table(
        "search_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
        ),
        sa.Column("course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="SET NULL")),
        sa.Column("topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="SET NULL")),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("normalized_query", sa.Text(), nullable=False),
        sa.Column("query_embedding", Vector(EMBEDDING_DIMENSIONS)),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column(
            "searched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_search_logs_course_searched", "search_logs", ["course_id", "searched_at"])
    op.create_index(
        "ix_search_logs_course_normalized", "search_logs", ["course_id", "normalized_query"]
    )
    op.create_table(
        "search_clusters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("topic_id", sa.Uuid(), sa.ForeignKey("topics.id", ondelete="SET NULL")),
        sa.Column("label", sa.Text(), nullable=False),
        sa.Column("search_count", sa.Integer(), nullable=False),
        sa.Column("unique_students", sa.Integer(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_table(
        "search_cluster_members",
        sa.Column(
            "cluster_id",
            sa.Uuid(),
            sa.ForeignKey("search_clusters.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "search_log_id",
            sa.BigInteger(),
            sa.ForeignKey("search_logs.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "suggested_actions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "course_id", sa.Uuid(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column(
            "cluster_id",
            sa.Uuid(),
            sa.ForeignKey("search_clusters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", action_status, server_default="open", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column(
            "generation_run_id", sa.Uuid(), sa.ForeignKey("generation_runs.id", ondelete="SET NULL")
        ),
    )


def downgrade() -> None:
    raise NotImplementedError("This complete-schema migration is intentionally irreversible.")
