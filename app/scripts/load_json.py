import json
import sys
from pathlib import Path

from sqlalchemy import text

from app.db import engine


VIDEO_INSERT_SQL = """
INSERT INTO videos (
    id,
    creator_id,
    video_created_at,
    views_count,
    likes_count,
    comments_count,
    reports_count,
    created_at,
    updated_at
) VALUES (
    :id,
    :creator_id,
    :video_created_at,
    :views_count,
    :likes_count,
    :comments_count,
    :reports_count,
    :created_at,
    :updated_at
)
ON CONFLICT (id) DO NOTHING;
"""

SNAPSHOT_INSERT_SQL = """
INSERT INTO video_snapshots (
    id,
    video_id,
    views_count,
    likes_count,
    comments_count,
    reports_count,
    delta_views_count,
    delta_likes_count,
    delta_comments_count,
    delta_reports_count,
    created_at,
    updated_at
) VALUES (
    :id,
    :video_id,
    :views_count,
    :likes_count,
    :comments_count,
    :reports_count,
    :delta_views_count,
    :delta_likes_count,
    :delta_comments_count,
    :delta_reports_count,
    :created_at,
    :updated_at
)
ON CONFLICT (id) DO NOTHING;
"""


def _normalize_videos_container(raw):
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict) and "videos" in raw and isinstance(raw["videos"], list):
        return raw["videos"]
    raise ValueError("Unsupported JSON structure: expected list or object with 'videos' key")


def load(path: str) -> None:
    json_path = Path(path)
    if not json_path.is_file():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    videos = _normalize_videos_container(raw_data)

    total_videos = 0
    total_snapshots = 0

    with engine.begin() as conn:
        for video in videos:
            video_params = {
                "id": video["id"],
                "creator_id": video["creator_id"],
                "video_created_at": video["video_created_at"],
                "views_count": video["views_count"],
                "likes_count": video["likes_count"],
                "comments_count": video["comments_count"],
                "reports_count": video["reports_count"],
                "created_at": video["created_at"],
                "updated_at": video["updated_at"],
            }

            conn.execute(text(VIDEO_INSERT_SQL), video_params)
            total_videos += 1

            snapshots = video.get("snapshots", []) or video.get("video_snapshots", [])
            video_id = video["id"]

            for snap in snapshots:
                snap_params = {
                    "id": snap["id"],
                    "video_id": video_id,
                    "views_count": snap["views_count"],
                    "likes_count": snap["likes_count"],
                    "comments_count": snap["comments_count"],
                    "reports_count": snap["reports_count"],
                    "delta_views_count": snap["delta_views_count"],
                    "delta_likes_count": snap["delta_likes_count"],
                    "delta_comments_count": snap["delta_comments_count"],
                    "delta_reports_count": snap["delta_reports_count"],
                    "created_at": snap["created_at"],
                    "updated_at": snap["updated_at"],
                }
                conn.execute(text(SNAPSHOT_INSERT_SQL), snap_params)
                total_snapshots += 1

    print(f"Loaded {total_videos} videos and {total_snapshots} snapshots from {json_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m app.scripts.load_json path/to/videos.json")
        sys.exit(1)

    load(sys.argv[1])
