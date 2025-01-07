-- Create test user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'test_user') THEN
      CREATE USER test_user WITH PASSWORD 'test_password';
   END IF;
END
$do$;

-- Create test database if not exists
SELECT 'CREATE DATABASE quizmaster_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'quizmaster_test')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE quizmaster_test TO test_user;
ALTER DATABASE quizmaster_test OWNER TO test_user;
