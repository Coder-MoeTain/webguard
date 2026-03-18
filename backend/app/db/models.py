"""
WebGuard RF - SQLAlchemy models
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="researcher")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    file_path = Column(String(512), nullable=False)
    file_format = Column(String(20), default="parquet")
    total_samples = Column(Integer, default=0)
    attack_samples = Column(Integer, default=0)
    benign_samples = Column(Integer, default=0)
    sqli_samples = Column(Integer, default=0)
    xss_samples = Column(Integer, default=0)
    csrf_samples = Column(Integer, default=0)
    status = Column(String(20), default="ready")
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_metadata = Column(JSON)


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(64), unique=True, nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    status = Column(String(20), default="pending")
    classification_mode = Column(String(20), default="multiclass")
    feature_mode = Column(String(30), default="payload_only")
    train_ratio = Column(Float, default=0.70)
    val_ratio = Column(Float, default=0.15)
    test_ratio = Column(Float, default=0.15)
    n_estimators = Column(Integer, default=200)
    max_depth = Column(Integer)
    min_samples_split = Column(Integer, default=2)
    min_samples_leaf = Column(Integer, default=1)
    max_features = Column(String(20), default="sqrt")
    random_state = Column(Integer, default=42)
    hyperparameter_tuning = Column(Boolean, default=False)
    progress_percent = Column(Integer, default=0)
    current_phase = Column(String(100))
    error_message = Column(Text)
    metrics_json = Column(JSON)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class Model(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    training_job_id = Column(Integer, ForeignKey("training_jobs.id"))
    file_path = Column(String(512), nullable=False)
    preprocessing_path = Column(String(512))
    version = Column(Integer, default=1)
    classification_mode = Column(String(20), nullable=False)
    feature_mode = Column(String(30), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ModelMetric(Base):
    __tablename__ = "model_metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    split_type = Column(String(20), nullable=False)
    accuracy = Column(Float)
    precision_macro = Column(Float)
    recall_macro = Column(Float)
    f1_macro = Column(Float)
    f1_weighted = Column(Float)
    roc_auc = Column(Float)
    false_positive_rate = Column(Float)
    false_negative_rate = Column(Float)
    per_class_metrics = Column(JSON)
    confusion_matrix = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
