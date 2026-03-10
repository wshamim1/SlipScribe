-- SlipScribe Database Schema v1
-- Migration: 001_initial_schema
-- Created: 2026-03-08

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Receipts table
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    merchant_name VARCHAR(255),
    purchase_date DATE,
    subtotal DECIMAL(12, 2),
    tax DECIMAL(12, 2),
    total DECIMAL(12, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Status: pending, processing, completed, failed, manual_review
    confidence DECIMAL(3, 2), -- 0.00 to 1.00
    ocr_text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_status CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'manual_review')),
    CONSTRAINT chk_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_receipts_user_id ON receipts(user_id);
CREATE INDEX idx_receipts_status ON receipts(status);
CREATE INDEX idx_receipts_purchase_date ON receipts(purchase_date);
CREATE INDEX idx_receipts_merchant_name ON receipts(merchant_name);
CREATE INDEX idx_receipts_user_purchase_date ON receipts(user_id, purchase_date DESC);

-- Receipt images table
CREATE TABLE receipt_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    storage_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    page_index INTEGER DEFAULT 0,
    width INTEGER,
    height INTEGER,
    file_size_bytes INTEGER,
    mime_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_receipt_images_receipt_id ON receipt_images(receipt_id);

-- Receipt line items table
CREATE TABLE receipt_line_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    name VARCHAR(500) NOT NULL,
    quantity DECIMAL(10, 3) DEFAULT 1.0,
    unit_price DECIMAL(12, 2),
    line_total DECIMAL(12, 2) NOT NULL,
    discount_flag BOOLEAN DEFAULT FALSE,
    raw_text TEXT, -- Original OCR text for this line
    confidence DECIMAL(3, 2), -- 0.00 to 1.00
    category VARCHAR(100), -- Auto-categorized
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_line_item_confidence CHECK (confidence IS NULL OR (confidence >= 0 AND confidence <= 1))
);

CREATE INDEX idx_receipt_line_items_receipt_id ON receipt_line_items(receipt_id);
CREATE INDEX idx_receipt_line_items_name ON receipt_line_items(name);
CREATE INDEX idx_receipt_line_items_category ON receipt_line_items(category);

-- Categories table
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    icon VARCHAR(50),
    color VARCHAR(7), -- Hex color code
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Merchant category rules table
CREATE TABLE merchant_category_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- NULL = global rule
    match_pattern VARCHAR(255) NOT NULL,
    match_type VARCHAR(20) DEFAULT 'exact',
    -- Match types: exact, contains, starts_with, regex
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_match_type CHECK (match_type IN ('exact', 'contains', 'starts_with', 'regex'))
);

CREATE INDEX idx_merchant_category_rules_user_id ON merchant_category_rules(user_id);
CREATE INDEX idx_merchant_category_rules_priority ON merchant_category_rules(priority DESC);

-- Processing jobs table
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    receipt_id UUID NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,
    -- Job types: ocr_extraction, llm_structuring, validation
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    -- Status: queued, running, completed, failed, retrying
    attempt INTEGER DEFAULT 1,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    metadata JSONB,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_job_status CHECK (status IN ('queued', 'running', 'completed', 'failed', 'retrying'))
);

CREATE INDEX idx_processing_jobs_receipt_id ON processing_jobs(receipt_id);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX idx_processing_jobs_created_at ON processing_jobs(created_at);

-- Budgets table
CREATE TABLE budgets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    monthly_limit DECIMAL(12, 2) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, category_id)
);

CREATE INDEX idx_budgets_user_id ON budgets(user_id);

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    receipt_id UUID REFERENCES receipts(id) ON DELETE CASCADE,
    alert_type VARCHAR(50) NOT NULL,
    -- Alert types: overspend, anomaly, duplicate, low_confidence
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info',
    -- Severity: info, warning, critical
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT chk_alert_type CHECK (alert_type IN ('overspend', 'anomaly', 'duplicate', 'low_confidence')),
    CONSTRAINT chk_severity CHECK (severity IN ('info', 'warning', 'critical'))
);

CREATE INDEX idx_alerts_user_id ON alerts(user_id);
CREATE INDEX idx_alerts_acknowledged ON alerts(acknowledged);
CREATE INDEX idx_alerts_created_at ON alerts(created_at DESC);

-- Spend snapshots (precomputed aggregates)
CREATE TABLE spend_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot_month VARCHAR(7) NOT NULL, -- YYYY-MM format
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    merchant_name VARCHAR(255),
    total_amount DECIMAL(12, 2) NOT NULL,
    receipt_count INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, snapshot_month, category_id, merchant_name)
);

CREATE INDEX idx_spend_snapshots_user_month ON spend_snapshots(user_id, snapshot_month);
CREATE INDEX idx_spend_snapshots_category ON spend_snapshots(category_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_receipts_updated_at BEFORE UPDATE ON receipts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_receipt_line_items_updated_at BEFORE UPDATE ON receipt_line_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_merchant_category_rules_updated_at BEFORE UPDATE ON merchant_category_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_budgets_updated_at BEFORE UPDATE ON budgets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default categories
INSERT INTO categories (name, icon, color) VALUES
    ('Groceries', '🛒', '#4CAF50'),
    ('Dining', '🍽️', '#FF9800'),
    ('Transportation', '🚗', '#2196F3'),
    ('Shopping', '🛍️', '#E91E63'),
    ('Utilities', '💡', '#9C27B0'),
    ('Healthcare', '⚕️', '#F44336'),
    ('Entertainment', '🎬', '#00BCD4'),
    ('Travel', '✈️', '#3F51B5'),
    ('Other', '📦', '#9E9E9E');

-- Comments for documentation
COMMENT ON TABLE receipts IS 'Stores receipt metadata and extracted fields';
COMMENT ON TABLE receipt_line_items IS 'Stores individual line items from receipts';
COMMENT ON TABLE processing_jobs IS 'Tracks OCR and AI extraction job status';
COMMENT ON TABLE spend_snapshots IS 'Precomputed monthly spending aggregates for dashboard performance';
COMMENT ON COLUMN receipts.confidence IS 'Overall extraction confidence score (0-1)';
COMMENT ON COLUMN receipt_line_items.confidence IS 'Line item extraction confidence score (0-1)';
