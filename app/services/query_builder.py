from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.nlp.query_schema import ParsedQuery, DateRange


SqlWithParams = Tuple[str, Dict[str, Any]]


def _apply_date_range(
    where: List[str],
    params: Dict[str, Any],
    alias: str,
    column: str,
    date_range: DateRange,
) -> None:
    start = date_range.start
    end = date_range.end

    if start and end:
        where.append(f"{alias}.{column}::date BETWEEN :start_date AND :end_date")
        params["start_date"] = start
        params["end_date"] = end
    elif start:
        where.append(f"{alias}.{column}::date >= :start_date")
        params["start_date"] = start
    elif end:
        where.append(f"{alias}.{column}::date <= :end_date")
        params["end_date"] = end


def _build_where_clause(where: List[str]) -> str:
    if not where:
        return ""
    return " WHERE " + " AND ".join(where)


def _build_special_distinct_videos_with_positive_delta(parsed: ParsedQuery) -> SqlWithParams:
    if parsed.entity != "snapshot":
        raise ValueError(
            'special="distinct_videos_with_positive_delta" поддерживается только при entity="snapshot"'
        )

    params: Dict[str, Any] = {}
    where: List[str] = ["s.delta_views_count > 0"]

    if parsed.date_range is not None:
        _apply_date_range(where, params, alias="s", column="created_at", date_range=parsed.date_range)


    where_sql = _build_where_clause(where)
    sql = f"""
SELECT COUNT(DISTINCT s.video_id) AS value
FROM video_snapshots AS s
{where_sql}
""".strip()

    return sql, params

def _build_special_snapshots_with_negative_delta_views(parsed: ParsedQuery) -> SqlWithParams:
    if parsed.entity != "snapshot":
        raise ValueError(
            'special="snapshots_with_negative_delta_views" поддерживается только при entity="snapshot"'
        )

    params: Dict[str, Any] = {}
    where: List[str] = ["s.delta_views_count < 0"]

    if parsed.date_range is not None:
        _apply_date_range(where, params, alias="s", column="created_at", date_range=parsed.date_range)

    where_sql = _build_where_clause(where)
    sql = f"""
SELECT COUNT(*) AS value
FROM video_snapshots AS s
{where_sql}
""".strip()

    return sql, params


def build_sql(parsed: ParsedQuery) -> SqlWithParams:
    if parsed.special == "distinct_videos_with_positive_delta":
        return _build_special_distinct_videos_with_positive_delta(parsed)
    if parsed.special == "snapshots_with_negative_delta_views":
        return _build_special_snapshots_with_negative_delta_views(parsed)


    params: Dict[str, Any] = {}
    where: List[str] = []

    # ---------------------
    # entity = "video"
    # ---------------------
    if parsed.entity == "video":
        table_alias = "v"
        table_name = "videos"

        if parsed.creator_id is not None:
            where.append(f"{table_alias}.creator_id = :creator_id")
            params["creator_id"] = parsed.creator_id

        if parsed.min_views is not None:
            where.append(f"{table_alias}.views_count > :min_views")
            params["min_views"] = parsed.min_views

        if parsed.date_range is not None:
            _apply_date_range(where, params, alias=table_alias, column="video_created_at", date_range=parsed.date_range)

        where_sql = _build_where_clause(where)

        if parsed.metric == "videos_count":
            select_expr = "COUNT(*)"
        elif parsed.metric == "sum_views_total":
            select_expr = "COALESCE(SUM(v.views_count), 0)"
        elif parsed.metric == "sum_likes_total":
            select_expr = "COALESCE(SUM(v.likes_count), 0)"
        else:
            raise ValueError(f"Unsupported metric {parsed.metric!r} for entity 'video'")

        sql = f"""
SELECT {select_expr} AS value
FROM {table_name} AS {table_alias}
{where_sql}
""".strip()

        return sql, params

    # ---------------------
    # entity = "snapshot"
    # ---------------------
    if parsed.entity == "snapshot":
        table_alias = "s"
        table_name = "video_snapshots"

        if parsed.date_range is not None:
            _apply_date_range(where, params, alias=table_alias, column="created_at", date_range=parsed.date_range)

        where_sql = _build_where_clause(where)

        if parsed.metric == "sum_views_delta":
            select_expr = "COALESCE(SUM(s.delta_views_count), 0)"
        elif parsed.metric == "videos_count":
            select_expr = "COUNT(*)"
        else:
            raise ValueError(f"Unsupported metric {parsed.metric!r} for entity 'snapshot' without special mode")

        sql = f"""
SELECT {select_expr} AS value
FROM {table_name} AS {table_alias}
{where_sql}
""".strip()

        return sql, params

    raise ValueError(f"Unsupported entity: {parsed.entity!r}")
