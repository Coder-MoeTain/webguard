"""Initial WebGuard RF schema.

Revision ID: 001_initial
Revises:
Create Date: 2025-03-18

Tables: users, datasets, training_jobs, models, model_metrics
"""

from alembic import op
import sqlalchemy as sa


revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "datasets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("file_format", sa.String(length=20), nullable=True),
        sa.Column("total_samples", sa.Integer(), nullable=True),
        sa.Column("attack_samples", sa.Integer(), nullable=True),
        sa.Column("benign_samples", sa.Integer(), nullable=True),
        sa.Column("sqli_samples", sa.Integer(), nullable=True),
        sa.Column("xss_samples", sa.Integer(), nullable=True),
        sa.Column("csrf_samples", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("extra_metadata", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "training_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("classification_mode", sa.String(length=20), nullable=True),
        sa.Column("feature_mode", sa.String(length=30), nullable=True),
        sa.Column("train_ratio", sa.Float(), nullable=True),
        sa.Column("val_ratio", sa.Float(), nullable=True),
        sa.Column("test_ratio", sa.Float(), nullable=True),
        sa.Column("n_estimators", sa.Integer(), nullable=True),
        sa.Column("max_depth", sa.Integer(), nullable=True),
        sa.Column("min_samples_split", sa.Integer(), nullable=True),
        sa.Column("min_samples_leaf", sa.Integer(), nullable=True),
        sa.Column("max_features", sa.String(length=20), nullable=True),
        sa.Column("random_state", sa.Integer(), nullable=True),
        sa.Column("hyperparameter_tuning", sa.Boolean(), nullable=True),
        sa.Column("progress_percent", sa.Integer(), nullable=True),
        sa.Column("current_phase", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.JSON(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id"),
    )
    op.create_table(
        "models",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("training_job_id", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.String(length=512), nullable=False),
        sa.Column("preprocessing_path", sa.String(length=512), nullable=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("classification_mode", sa.String(length=20), nullable=False),
        sa.Column("feature_mode", sa.String(length=30), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["training_job_id"],
            ["training_jobs.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id"),
    )
    op.create_table(
        "model_metrics",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_id", sa.Integer(), nullable=True),
        sa.Column("split_type", sa.String(length=20), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=True),
        sa.Column("precision_macro", sa.Float(), nullable=True),
        sa.Column("recall_macro", sa.Float(), nullable=True),
        sa.Column("f1_macro", sa.Float(), nullable=True),
        sa.Column("f1_weighted", sa.Float(), nullable=True),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("false_positive_rate", sa.Float(), nullable=True),
        sa.Column("false_negative_rate", sa.Float(), nullable=True),
        sa.Column("per_class_metrics", sa.JSON(), nullable=True),
        sa.Column("confusion_matrix", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["model_id"],
            ["models.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("model_metrics")
    op.drop_table("models")
    op.drop_table("training_jobs")
    op.drop_table("datasets")
    op.drop_table("users")
