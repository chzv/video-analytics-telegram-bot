-- Migration: create videos and video_snapshots tables for video analytics bot

CREATE TABLE IF NOT EXISTS videos (
    id TEXT PRIMARY KEY,
    creator_id TEXT NOT NULL,
    video_created_at TIMESTAMPTZ NOT NULL,
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS video_snapshots (
    id TEXT PRIMARY KEY,
    video_id TEXT NOT NULL REFERENCES videos(id),
    views_count BIGINT NOT NULL,
    likes_count BIGINT NOT NULL,
    comments_count BIGINT NOT NULL,
    reports_count BIGINT NOT NULL,
    delta_views_count BIGINT NOT NULL,
    delta_likes_count BIGINT NOT NULL,
    delta_comments_count BIGINT NOT NULL,
    delta_reports_count BIGINT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_videos_creator_created
    ON videos (creator_id, video_created_at);

CREATE INDEX IF NOT EXISTS idx_videos_views
    ON videos (views_count);

CREATE INDEX IF NOT EXISTS idx_snapshots_created
    ON video_snapshots (created_at);

CREATE INDEX IF NOT EXISTS idx_snapshots_video
    ON video_snapshots (video_id, created_at);
