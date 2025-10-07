-- sudo users
CREATE TABLE IF NOT EXISTS sudo_users (
  user_id BIGINT PRIMARY KEY
);

-- global commands: /start & /help
CREATE TABLE IF NOT EXISTS global_commands (
  id SERIAL PRIMARY KEY,
  start_enabled BOOLEAN NOT NULL DEFAULT FALSE,
  help_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
  start_text    TEXT NOT NULL DEFAULT '',
  help_text     TEXT NOT NULL DEFAULT '',
  updated_by    BIGINT,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- groups registry
CREATE TABLE IF NOT EXISTS groups (
  chat_id BIGINT PRIMARY KEY,
  title   TEXT,
  approved BOOLEAN DEFAULT FALSE,
  pending_approval BOOLEAN DEFAULT TRUE,
  id SERIAL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- per-group features: rules / welcome
CREATE TABLE IF NOT EXISTS group_feature (
  id SERIAL PRIMARY KEY,
  chat_id BIGINT NOT NULL,
  feature TEXT NOT NULL CHECK (feature IN ('rules','welcome')),
  enabled BOOLEAN NOT NULL DEFAULT FALSE,
  text TEXT,
  media_kind TEXT,
  media_pointer TEXT,
  buttons_json TEXT,
  updated_by BIGINT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(chat_id, feature)
);