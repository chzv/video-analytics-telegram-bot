from .query_schema import ParsedQuery


def build_prompt(user_text: str) -> str:

    schema_description = f"""
You are a system that maps Russian analytics questions about video statistics
to a strict JSON specification.

Database schema:

Table "videos" (final statistics for each video):
- id               : TEXT, primary key, unique video ID
- creator_id       : TEXT, creator ID
- video_created_at : TIMESTAMPTZ, publication datetime of the video
- views_count      : BIGINT, final total number of views for this video
- likes_count      : BIGINT, final total number of likes
- comments_count   : BIGINT, final total number of comments
- reports_count    : BIGINT, final total number of reports
- created_at       : TIMESTAMPTZ, service field (row created in DB)
- updated_at       : TIMESTAMPTZ, service field (row updated in DB)

Table "video_snapshots" (hourly statistics snapshots for each video):
- id                   : TEXT, primary key
- video_id             : TEXT, foreign key to videos(id)
- views_count          : BIGINT, current total views at snapshot time
- likes_count          : BIGINT, current total likes at snapshot time
- comments_count       : BIGINT, current total comments at snapshot time
- reports_count        : BIGINT, current total reports at snapshot time
- delta_views_count    : BIGINT, change in views_count since previous snapshot
- delta_likes_count    : BIGINT, change in likes_count since previous snapshot
- delta_comments_count : BIGINT, change in comments_count since previous snapshot
- delta_reports_count  : BIGINT, change in reports_count since previous snapshot
- created_at           : TIMESTAMPTZ, snapshot datetime (once per hour)
- updated_at           : TIMESTAMPTZ, service field

You must map each Russian question to a JSON object that matches
the following Pydantic schema (Python description):

class DateRange(BaseModel):
    start: Optional[str]  # ISO 8601 date string "YYYY-MM-DD"
    end: Optional[str]    # ISO 8601 date string "YYYY-MM-DD"

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
    special: Optional[Literal["distinct_videos_with_positive_delta"]] = None

Field semantics:

- metric:
    - "videos_count":
        Count videos that match filters (SELECT COUNT(*) FROM videos ...).
    - "sum_views_delta":
        Sum the delta_views_count field from video_snapshots
        (e.g. total growth of views for a given day).
    - "sum_views_total":
        Sum the views_count field (final total) from videos table.
    - "sum_likes_total":
        Sum the likes_count field (final total) from videos table.

- entity:
    - "video"    : use "videos" table as the primary source.
    - "snapshot" : use "video_snapshots" table as the primary source.

- creator_id:
    Filter by creator_id = this value (for videos). This is a string identifier,
    for example "aca1061a9d324ecf8c3fa2bb32d7be63".

- min_views:
    Filter videos with views_count > min_views.

- date_range:
    A range of dates (not datetimes), inclusive.
    start and end MUST be ISO strings "YYYY-MM-DD".

    When metric is "videos_count" and entity="video":
        - date_range refers to videos.video_created_at::date BETWEEN start and end.

    When metric is "sum_views_delta" and entity="snapshot":
        - date_range refers to video_snapshots.created_at::date BETWEEN start and end.

- special:
    - "distinct_videos_with_positive_delta":
        Used for questions like
        "Сколько разных видео получали новые просмотры 27 ноября 2025?"
        It means:
        count distinct video_id in video_snapshots
        where delta_views_count > 0 for the requested date_range.

The user will ask questions in Russian. Dates can be written in Russian,
for example: "28 ноября 2025", "с 1 по 5 ноября 2025" and so on.

You MUST:
1. Understand the question.
2. Choose appropriate metric and entity.
3. Fill filters: creator_id, min_views, date_range, special when needed.
4. Convert all dates to ISO date strings in format "YYYY-MM-DD"
   (no time part), inside date_range.start and date_range.end.
5. If some field is not needed, set it to null (in JSON).

You MUST return ONLY a single JSON object that matches ParsedQuery.
Do NOT include comments, code fences, explanations, or any extra text.

EXAMPLES (very important):

Example 1:
Q: "Сколько всего видео есть в системе?"
A:
{{
  "metric": "videos_count",
  "entity": "video",
  "creator_id": null,
  "min_views": null,
  "date_range": null,
  "special": null
}}

Example 2:
Q: "Сколько видео у креатора с id 123 вышло с 1 ноября 2025 по 5 ноября 2025 включительно?"
A:
{{
  "metric": "videos_count",
  "entity": "video",
  "creator_id": "123",
  "min_views": null,
  "date_range": {{
    "start": "2025-11-01",
    "end": "2025-11-05"
  }},
  "special": null
}}

Example 3:
Q: "Сколько видео набрало больше 100 000 просмотров за всё время?"
A:
{{
  "metric": "videos_count",
  "entity": "video",
  "creator_id": null,
  "min_views": 100000,
  "date_range": null,
  "special": null
}}

Example 4:
Q: "На сколько просмотров в сумме выросли все видео 28 ноября 2025?"
A:
{{
  "metric": "sum_views_delta",
  "entity": "snapshot",
  "creator_id": null,
  "min_views": null,
  "date_range": {{
    "start": "2025-11-28",
    "end": "2025-11-28"
  }},
  "special": null
}}

Example 5:
Q: "Сколько разных видео получали новые просмотры 27 ноября 2025?"
A:
{{
  "metric": "videos_count",
  "entity": "snapshot",
  "creator_id": null,
  "min_views": null,
  "date_range": {{
    "start": "2025-11-27",
    "end": "2025-11-27"
  }},
  "special": "distinct_videos_with_positive_delta"
}}

Example 6:
Q: "Сколько видео у креатора с id aca1061a9d324ecf8c3fa2bb32d7be63 набрали больше 10 000 просмотров по итоговой статистике?"
A:
{{
  "metric": "videos_count",
  "entity": "video",
  "creator_id": "aca1061a9d324ecf8c3fa2bb32d7be63",
  "min_views": 10000,
  "date_range": null,
  "special": null
}}

Now the real user question in Russian is:

"{user_text}"

Return ONLY the JSON object for ParsedQuery, with double quotes for all keys
and string values, and with null instead of missing fields.
"""

    return schema_description
