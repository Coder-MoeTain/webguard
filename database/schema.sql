-- WebGuard RF - Database Schema
-- MySQL 8.0+ / MariaDB 10.5+

CREATE DATABASE IF NOT EXISTS webguard_rf CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE webguard_rf;

-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'researcher', 'viewer') DEFAULT 'researcher',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- Datasets table
CREATE TABLE datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(512) NOT NULL,
    file_format ENUM('csv', 'parquet') DEFAULT 'parquet',
    total_samples INT DEFAULT 0,
    attack_samples INT DEFAULT 0,
    benign_samples INT DEFAULT 0,
    sqli_samples INT DEFAULT 0,
    xss_samples INT DEFAULT 0,
    csrf_samples INT DEFAULT 0,
    status ENUM('generating', 'uploading', 'ready', 'failed') DEFAULT 'ready',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Training jobs table
CREATE TABLE training_jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(64) UNIQUE NOT NULL,
    dataset_id INT,
    status ENUM('pending', 'running', 'completed', 'failed', 'cancelled') DEFAULT 'pending',
    classification_mode ENUM('binary', 'multiclass') DEFAULT 'multiclass',
    feature_mode VARCHAR(30) DEFAULT 'payload_only',
    train_ratio DECIMAL(4,2) DEFAULT 0.70,
    val_ratio DECIMAL(4,2) DEFAULT 0.15,
    test_ratio DECIMAL(4,2) DEFAULT 0.15,
    n_estimators INT DEFAULT 200,
    max_depth INT DEFAULT 30,
    min_samples_split INT DEFAULT 2,
    min_samples_leaf INT DEFAULT 1,
    max_features VARCHAR(20) DEFAULT 'sqrt',
    random_state INT DEFAULT 42,
    hyperparameter_tuning BOOLEAN DEFAULT FALSE,
    progress_percent INT DEFAULT 0,
    current_phase VARCHAR(100),
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
);

-- Experiments table (links to training jobs)
CREATE TABLE experiments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    training_job_id INT,
    experiment_type ENUM('payload_only', 'hybrid', 'ablation') DEFAULT 'payload_only',
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (training_job_id) REFERENCES training_jobs(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_created_at (created_at)
);

-- Models table
CREATE TABLE models (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    training_job_id INT,
    file_path VARCHAR(512) NOT NULL,
    preprocessing_path VARCHAR(512),
    version INT DEFAULT 1,
    classification_mode ENUM('binary', 'multiclass') NOT NULL,
    feature_mode VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (training_job_id) REFERENCES training_jobs(id) ON DELETE SET NULL,
    INDEX idx_model_id (model_id),
    INDEX idx_created_at (created_at)
);

-- Model metrics table
CREATE TABLE model_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT,
    split_type ENUM('train', 'validation', 'test') NOT NULL,
    accuracy DECIMAL(6,4),
    precision_macro DECIMAL(6,4),
    recall_macro DECIMAL(6,4),
    f1_macro DECIMAL(6,4),
    f1_weighted DECIMAL(6,4),
    roc_auc DECIMAL(6,4),
    false_positive_rate DECIMAL(6,4),
    false_negative_rate DECIMAL(6,4),
    per_class_metrics JSON,
    confusion_matrix JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    INDEX idx_model_split (model_id, split_type)
);

-- Feature importance table
CREATE TABLE feature_importance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT,
    feature_name VARCHAR(255) NOT NULL,
    importance DECIMAL(10,6) NOT NULL,
    rank INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    INDEX idx_model_id (model_id)
);

-- Inference logs table
CREATE TABLE inference_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT,
    payload_hash VARCHAR(64),
    prediction VARCHAR(50) NOT NULL,
    confidence DECIMAL(6,4),
    top_features JSON,
    request_data JSON,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_created_at (created_at),
    INDEX idx_prediction (prediction)
);

-- Payload test results (robustness testing)
CREATE TABLE payload_test_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    model_id INT,
    test_suite VARCHAR(100) NOT NULL,
    total_tests INT,
    passed INT,
    failed INT,
    false_positives INT,
    false_negatives INT,
    results_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    INDEX idx_model_id (model_id)
);

-- System logs (audit)
CREATE TABLE system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSON,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
);

-- Seed admin user (password: admin123 - CHANGE IN PRODUCTION)
-- Generate hash with: python -c "import bcrypt; print(bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode())"
INSERT INTO users (username, email, hashed_password, role) VALUES
('admin', 'admin@webguard.local', '$2b$12$H/MoxypiAbNWPVtYV2FMjeJ6LKPNWtq1h1z6i2c.HP2D2vsyndv2a', 'admin');
