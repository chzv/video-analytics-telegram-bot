from app.nlp.query_schema import ParsedQuery, DateRange
from app.services.query_builder import build_sql


def _normalize_sql(sql: str) -> str:
    return " ".join(sql.split())


def test_videos_count_all_videos():
    parsed = ParsedQuery(
        metric="videos_count",
        entity="video",
        creator_id=None,
        min_views=None,
        date_range=None,
        special=None,
    )

    sql, params = build_sql(parsed)
    norm = _normalize_sql(sql)

    assert "SELECT COUNT(*) AS value" in norm
    assert "FROM videos AS v" in norm
    assert " WHERE " not in norm
    assert params == {}


def test_videos_count_with_min_views():
    parsed = ParsedQuery(
        metric="videos_count",
        entity="video",
        creator_id=None,
        min_views=100000,
        date_range=None,
        special=None,
    )

    sql, params = build_sql(parsed)
    norm = _normalize_sql(sql)

    assert "SELECT COUNT(*) AS value" in norm
    assert "FROM videos AS v" in norm
    assert "v.views_count > :min_views" in norm
    assert params == {"min_views": 100000}


def test_sum_views_delta_single_date():
    parsed = ParsedQuery(
        metric="sum_views_delta",
        entity="snapshot",
        creator_id=None,
        min_views=None,
        date_range=DateRange(start="2025-11-28", end="2025-11-28"),
        special=None,
    )

    sql, params = build_sql(parsed)
    norm = _normalize_sql(sql)

    assert "SELECT COALESCE(SUM(s.delta_views_count), 0) AS value" in norm
    assert "FROM video_snapshots AS s" in norm
    assert "s.created_at::date BETWEEN :start_date AND :end_date" in norm
    assert params == {
        "start_date": "2025-11-28",
        "end_date": "2025-11-28",
    }


def test_special_distinct_videos_with_positive_delta():
    parsed = ParsedQuery(
        metric="videos_count",
        entity="snapshot",
        creator_id=None,
        min_views=None,
        date_range=DateRange(start="2025-11-27", end="2025-11-27"),
        special="distinct_videos_with_positive_delta",
    )

    sql, params = build_sql(parsed)
    norm = _normalize_sql(sql)

    assert "SELECT COUNT(DISTINCT s.video_id) AS value" in norm
    assert "FROM video_snapshots AS s" in norm
    assert "s.delta_views_count > 0" in norm
    assert "s.created_at::date BETWEEN :start_date AND :end_date" in norm
    assert params == {
        "start_date": "2025-11-27",
        "end_date": "2025-11-27",
    }
