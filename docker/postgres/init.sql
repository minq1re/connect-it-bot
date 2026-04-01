-- Инициализация схемы ConnectIT.
-- Важно: этот скрипт выполняется внутри БД, указанной как POSTGRES_DB (connectit_db).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(64),
    first_name VARCHAR(128),
    last_name VARCHAR(128),
    age INTEGER,
    city VARCHAR(128),
    bio TEXT,
    skills TEXT,
    about_me TEXT,
    avatar_url VARCHAR(512),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_telegram_id ON users (telegram_id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users (username);
CREATE INDEX IF NOT EXISTS ix_users_age ON users (age);
CREATE INDEX IF NOT EXISTS ix_users_city ON users (city);
CREATE INDEX IF NOT EXISTS ix_users_is_active ON users (is_active);
CREATE INDEX IF NOT EXISTS ix_users_is_blocked ON users (is_blocked);

ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_blocked BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS likes (
    id BIGSERIAL PRIMARY KEY,
    from_user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    to_user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_like_pair UNIQUE (from_user_id, to_user_id),
    CONSTRAINT ck_like_not_self CHECK (from_user_id <> to_user_id)
);

CREATE INDEX IF NOT EXISTS ix_likes_from_user_id ON likes (from_user_id);
CREATE INDEX IF NOT EXISTS ix_likes_to_user_id ON likes (to_user_id);
CREATE INDEX IF NOT EXISTS ix_likes_from_created ON likes (from_user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_likes_to_created ON likes (to_user_id, created_at);

CREATE TABLE IF NOT EXISTS dislikes (
    id BIGSERIAL PRIMARY KEY,
    from_user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    to_user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dislike_pair UNIQUE (from_user_id, to_user_id),
    CONSTRAINT ck_dislike_not_self CHECK (from_user_id <> to_user_id)
);

CREATE INDEX IF NOT EXISTS ix_dislikes_from_user_id ON dislikes (from_user_id);
CREATE INDEX IF NOT EXISTS ix_dislikes_to_user_id ON dislikes (to_user_id);
CREATE INDEX IF NOT EXISTS ix_dislikes_from_created ON dislikes (from_user_id, created_at);
CREATE INDEX IF NOT EXISTS ix_dislikes_to_created ON dislikes (to_user_id, created_at);

CREATE TABLE IF NOT EXISTS matches (
    id BIGSERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    user2_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_match_pair UNIQUE (user1_id, user2_id),
    CONSTRAINT ck_match_order CHECK (user1_id < user2_id)
);

CREATE INDEX IF NOT EXISTS ix_matches_user1_id ON matches (user1_id);
CREATE INDEX IF NOT EXISTS ix_matches_user2_id ON matches (user2_id);
CREATE INDEX IF NOT EXISTS ix_matches_user1_created ON matches (user1_id, created_at);
CREATE INDEX IF NOT EXISTS ix_matches_user2_created ON matches (user2_id, created_at);

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_status') THEN
        CREATE TYPE report_status AS ENUM ('open', 'reviewing', 'resolved', 'rejected');
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS reports (
    id BIGSERIAL PRIMARY KEY,
    reporter_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    reported_user_id BIGINT NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    reason VARCHAR(255) NOT NULL,
    details TEXT,
    status report_status NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_report_not_self CHECK (reporter_id <> reported_user_id)
);

CREATE INDEX IF NOT EXISTS ix_reports_reporter_id ON reports (reporter_id);
CREATE INDEX IF NOT EXISTS ix_reports_reported_user_id ON reports (reported_user_id);
CREATE INDEX IF NOT EXISTS ix_reports_reported_status ON reports (reported_user_id, status);
CREATE INDEX IF NOT EXISTS ix_reports_reporter_created ON reports (reporter_id, created_at);

COMMENT ON TABLE users IS 'Профили пользователей ConnectIT';
COMMENT ON TABLE likes IS 'Лайки между пользователями';
COMMENT ON TABLE dislikes IS 'Дизлайки между пользователями';
COMMENT ON TABLE matches IS 'Взаимные мэтчи пользователей';
COMMENT ON TABLE reports IS 'Жалобы пользователей на других пользователей';
