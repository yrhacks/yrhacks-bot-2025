DROP TABLE IF EXISTS team_invites CASCADE;
DROP TABLE IF EXISTS teams CASCADE;
DROP TABLE IF EXISTS users CASCADE;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    discord_id BIGINT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    school TEXT NOT NULL,
    grade TEXT NOT NULL,
    shsm_sector TEXT DEFAULT 'None',
    about TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
);

CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    owner_id BIGINT NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- Add team_id column after teams table exists because of the circular reference
ALTER TABLE users
ADD COLUMN team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL;

CREATE TABLE team_invites (
    id SERIAL PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id) ON DELETE CASCADE,
    user_id BIGINT NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    invited_by BIGINT NOT NULL REFERENCES users(discord_id) ON DELETE CASCADE,
    status TEXT CHECK (status IN ('pending', 'accepted', 'declined')) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    UNIQUE (team_id, user_id)
);

CREATE OR REPLACE FUNCTION invite_user_to_team(inviter_id BIGINT, invitee_id BIGINT)
RETURNS VOID AS $$
BEGIN
    INSERT INTO team_invites (team_id, user_id)
    SELECT team_id, invitee_id
    FROM users
    WHERE discord_id = inviter_id
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fetch_teams_with_counts()
RETURNS TABLE (
    id INTEGER, 
    name TEXT, 
    owner_id BIGINT, 
    created_at TIMESTAMP, 
    updated_at TIMESTAMP, 
    member_count INTEGER
) AS $$
BEGIN
    RETURN QUERY 
    SELECT t.id, t.name, t.owner_id, t.created_at, t.updated_at, COUNT(u.id)::INTEGER AS member_count
    FROM teams t
    LEFT JOIN users u ON t.id = u.team_id
    GROUP BY t.id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fetch_team_with_count(p_team_id INTEGER)
RETURNS TABLE (
    id INTEGER, 
    name TEXT, 
    owner_id BIGINT, 
    created_at TIMESTAMP, 
    updated_at TIMESTAMP, 
    member_count INTEGER
) AS $$
BEGIN
    RETURN QUERY 
    SELECT t.id, t.name, t.owner_id, t.created_at, t.updated_at, COUNT(u.id)::INTEGER AS member_count
    FROM teams t
    LEFT JOIN users u ON t.id = u.team_id
    WHERE t.id = p_team_id
    GROUP BY t.id;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION fetch_pending_invites(member_id BIGINT)
RETURNS TABLE (
    id INTEGER, 
    name TEXT, 
    owner_id BIGINT, 
    created_at TIMESTAMP, 
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT t.*
    FROM teams t
    JOIN team_invites ti ON t.id = ti.team_id
    WHERE ti.user_id = member_id AND ti.status = 'pending';
END;
$$ LANGUAGE plpgsql;
