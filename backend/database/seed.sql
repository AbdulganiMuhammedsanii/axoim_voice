-- Seed data for development and testing
-- Run this after creating the schema

-- Insert a sample organization
INSERT INTO organizations (id, name, business_hours, after_hours_policy, services_offered, escalation_phone, config)
VALUES (
    'org_demo_001',
    'Axiom Labs',
    'Monday-Friday, 9:00 AM - 5:00 PM',
    'voicemail',
    'Consultations
Technical Support
Product Inquiries
Scheduling',
    '+1 (555) 100-2000',
    '{}'::jsonb
)
ON CONFLICT (id) DO NOTHING;

-- You can add more sample organizations or test data here

