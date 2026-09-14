CREATE TABLE IF NOT EXISTS business_units (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS teams (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  business_unit_id BIGINT REFERENCES business_units(id)
);

CREATE TABLE IF NOT EXISTS repositories (
  id BIGSERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  path TEXT NOT NULL,
  type TEXT NOT NULL,
  criticality TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS services (
  id BIGSERIAL PRIMARY KEY,
  repository_id BIGINT NOT NULL REFERENCES repositories(id),
  team_id BIGINT REFERENCES teams(id),
  domain TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS repository_relationships (
  id BIGSERIAL PRIMARY KEY,
  source_repository TEXT NOT NULL,
  relationship_type TEXT NOT NULL,
  target TEXT NOT NULL,
  evidence TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS capabilities (
  id BIGSERIAL PRIMARY KEY,
  repository_id BIGINT NOT NULL REFERENCES repositories(id),
  capability TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
  id BIGSERIAL PRIMARY KEY,
  repository_id BIGINT NOT NULL REFERENCES repositories(id),
  path TEXT NOT NULL,
  body TEXT NOT NULL
);
