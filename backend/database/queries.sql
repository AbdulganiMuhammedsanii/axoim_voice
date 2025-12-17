-- Useful queries to view data in your database

-- View all organizations
SELECT * FROM organizations;

-- View all calls
SELECT 
    id,
    org_id,
    started_at,
    ended_at,
    status,
    escalated,
    EXTRACT(EPOCH FROM (ended_at - started_at))::int AS duration_seconds
FROM calls
ORDER BY started_at DESC
LIMIT 20;

-- View calls with organization name
SELECT 
    c.id,
    c.org_id,
    o.name AS organization_name,
    c.started_at,
    c.ended_at,
    c.status,
    c.escalated
FROM calls c
LEFT JOIN organizations o ON c.org_id = o.id
ORDER BY c.started_at DESC;

-- View call transcripts for a specific call
SELECT 
    ct.speaker,
    ct.text,
    ct.timestamp
FROM call_transcripts ct
WHERE ct.call_id = 'YOUR_CALL_ID_HERE'
ORDER BY ct.timestamp;

-- View all transcripts (latest first)
SELECT 
    ct.call_id,
    ct.speaker,
    ct.text,
    ct.timestamp,
    c.org_id
FROM call_transcripts ct
LEFT JOIN calls c ON ct.call_id = c.id
ORDER BY ct.timestamp DESC
LIMIT 50;

-- View call intakes
SELECT 
    ci.call_id,
    ci.structured_json,
    ci.urgency_level,
    ci.completed,
    ci.created_at
FROM call_intakes ci
ORDER BY ci.created_at DESC;

-- View complete call details (call + transcripts + intake)
SELECT 
    c.id AS call_id,
    c.org_id,
    o.name AS org_name,
    c.started_at,
    c.ended_at,
    c.status,
    c.escalated,
    (SELECT COUNT(*) FROM call_transcripts WHERE call_id = c.id) AS transcript_count,
    ci.urgency_level,
    ci.completed AS intake_completed
FROM calls c
LEFT JOIN organizations o ON c.org_id = o.id
LEFT JOIN call_intakes ci ON ci.call_id = c.id
ORDER BY c.started_at DESC;

-- Count calls by status
SELECT 
    status,
    COUNT(*) AS count
FROM calls
GROUP BY status;

-- Count calls by organization
SELECT 
    o.name AS organization,
    COUNT(c.id) AS call_count
FROM organizations o
LEFT JOIN calls c ON c.org_id = o.id
GROUP BY o.name
ORDER BY call_count DESC;

