-- Runs once on first Postgres initialization (empty data volume).
-- Creates a separate database used by the pytest suite so tests never touch
-- the application's data.
CREATE DATABASE appointments_test;
