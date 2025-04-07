from __future__ import annotations

from typing import TypedDict

class Registration(TypedDict):
    discord_username: str
    school: str
    grade: str
    full_name: str
    shsm_sector: str

class TeamRecord(TypedDict):
    id: int
    name: str
    owner_id: int
    created_at: str
    updated_at: str

class TeamRecordWithCounts(TeamRecord):
    member_count: int

class UserRecord(TypedDict):
    id: int
    discord_id: int
    full_name: str
    school: str
    grade: str
    about: str | None
    shsm_sector: str
    team_id: int | None
    created_at: str
    updated_at: str
