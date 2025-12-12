from __future__ import annotations

from sqlalchemy import text

from app.db import get_session
from app.nlp.query_schema import ParsedQuery
from .query_builder import build_sql


def execute_analytics_query(parsed: ParsedQuery) -> int:
    sql, params = build_sql(parsed)

    with get_session() as session:
        result = session.execute(text(sql), params).scalar()
        return int(result or 0)
