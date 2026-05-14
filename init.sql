-- ShakthiDB Initialization Script
-- This creates the schema required for the AICyberAuditBox application

CREATE TABLE IF NOT EXISTS audit_findings (
    id SERIAL PRIMARY KEY,
    use_case_sl INTEGER,
    use_case_name VARCHAR(300),
    severity VARCHAR(50),
    control VARCHAR(200),
    finding TEXT,
    recommendation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
