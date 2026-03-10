-- Dev seed data — run once after migrations
-- Matches MOCK_USER_ID in backend/app/api/v1/endpoints/receipts.py

INSERT INTO users (id, email, password_hash, full_name, created_at, updated_at)
VALUES (
    'a1000000-0000-0000-0000-000000000001',
    'dev@slipscribe.local',
    'mock_hash_not_for_auth',
    'Dev User',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;
