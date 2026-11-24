-- Runs once, on first initialisation of the postgres_data volume (docker-entrypoint-initdb.d).
-- The docqa database itself is created by POSTGRES_DB. To re-run this, remove the volume:
--   docker compose -f infra/docker/docker-compose.yml down -v

CREATE DATABASE temporal OWNER docqa;
CREATE DATABASE temporal_visibility OWNER docqa;
CREATE DATABASE langfuse OWNER docqa;

GRANT ALL PRIVILEGES ON DATABASE temporal TO docqa;
GRANT ALL PRIVILEGES ON DATABASE temporal_visibility TO docqa;
GRANT ALL PRIVILEGES ON DATABASE langfuse TO docqa;
