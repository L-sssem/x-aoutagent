"""Database models for Supabase tables."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID


@dataclass(slots=True)
class Account:
    id: UUID
    account_id: str
    display_name: str | None
    phase: str | None
    is_shadowbanned: bool
    ai_provider: str | None
    ai_model: str | None
    forbidden_content: list[str]
    forbidden_actions: list[str]
    post_frequency: int | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Post:
    id: UUID
    account_id: str
    content: str
    purpose: str | None
    media_paths: list[str]
    scheduled_at: datetime | None
    posted_at: datetime | None
    is_posted: bool
    is_failed: bool
    likes: int
    retweets: int
    replies: int
    bookmarks: int
    impressions: int
    tweet_id: str | None
    created_at: datetime


@dataclass(slots=True)
class Knowledge:
    id: UUID
    scope: str
    account_id: str | None
    content: str
    confidence: str
    category: str | None
    validation_count: int
    last_validated_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(slots=True)
class Tactic:
    id: UUID
    account_id: str
    description: str
    knowledge_id: UUID | None
    success_count: int
    fail_count: int
    score_threshold: int
    created_at: datetime


@dataclass(slots=True)
class DailyReport:
    id: UUID
    account_id: str
    report_date: date
    reflection: str | None
    hypothesis: str | None
    pm_instruction: str | None
    created_at: datetime


@dataclass(slots=True)
class WeeklyReport:
    id: UUID
    week_start: date
    follower_summary: dict[str, Any] | None
    impression_summary: dict[str, Any] | None
    tactics_summary: str | None
    evaluation: str | None
    next_week_plan: str | None
    created_at: datetime


@dataclass(slots=True)
class Schedule:
    id: UUID
    account_id: str
    post_id: UUID | None
    scheduled_at: datetime
    is_checked: bool
    created_at: datetime


@dataclass(slots=True)
class Notification:
    id: UUID
    type: str
    account_id: str | None
    message: str
    is_read: bool
    created_at: datetime


@dataclass(slots=True)
class AIActionModel:
    id: UUID
    action_name: str
    ai_provider: str
    ai_model: str
    updated_at: datetime
