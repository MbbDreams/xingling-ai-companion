from datetime import datetime
from pydantic import BaseModel, Field


class GrowthSummary(BaseModel):
    intimacy_level: int = Field(default=1, description="亲密度等级")
    intimacy_points: int = Field(default=0, description="亲密度积分")
    intimacy_for_next: int = Field(default=100, description="距离下一级还需")
    total_messages: int = Field(default=0, description="总消息数")
    milestones_count: int = Field(default=0, description="已达成里程碑数")
    active_days: int = Field(default=0, description="活跃天数")


class MilestoneResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    achieved_at: datetime
