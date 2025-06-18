# app/schemas/report_schema.py

from pydantic import BaseModel

class DailyReportResponse(BaseModel):
    total_sleep_minutes: int
    total_feeds: int
    longest_nap_minutes: int


class DailyReportOut(BaseModel):
    date: str
    total_sleep_minutes: int
    longest_nap_minutes: int