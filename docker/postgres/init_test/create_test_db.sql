-- Create a dedicated test database for integration tests (run on container init)
CREATE DATABASE "HMS_TEST";
GRANT ALL PRIVILEGES ON DATABASE "HMS_TEST" TO "QA_Test";
