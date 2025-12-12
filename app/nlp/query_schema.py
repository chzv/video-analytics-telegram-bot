from typing import Literal, Optional

from pydantic import BaseModel


class DateRange(BaseModel):

    start: Optional[str]  # ISO 8601 string: "YYYY-MM-DD"
    end: Optional[str]    # ISO 8601 string: "YYYY-MM-DD"


class ParsedQuery(BaseModel):
    metric: Literal[
        "videos_count",
        "sum_views_delta",
        "sum_views_total",
        "sum_likes_total",
    ]

    entity: Literal["video", "snapshot"]

    creator_id: Optional[str] = None
    min_views: Optional[int] = None
    date_range: Optional[DateRange] = None

    special: Optional[Literal[
        "distinct_videos_with_positive_delta",
        "snapshots_with_negative_delta_views",
    ]] = None
