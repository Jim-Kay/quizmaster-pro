-- Insert mock user if it doesn't exist
INSERT INTO users (id, email, name)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'jkay65@gmail.com',
    'Development User'
)
ON CONFLICT (id) DO NOTHING;
