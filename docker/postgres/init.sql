DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'connectit_user') THEN
      CREATE USER connectit_user WITH PASSWORD 'connectit_password';
   END IF;
END
$do$;

CREATE DATABASE connectit_db OWNER connectit_user;

\c connectit_db;

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
