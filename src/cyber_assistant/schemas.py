from __future__ import annotations

import re
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class IncidentSearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str | None = Field(default=None, max_length=500, description="Free-text incident or keyword query")
    attack_label: str | None = Field(default=None, max_length=100, description="Exact attack label")
    attack_family: str | None = Field(default=None, max_length=100, description="Attack family category")
    protocol: int | None = Field(default=None, ge=0, le=255, description="IP protocol number (6=TCP, 17=UDP)")
    source_file: str | None = Field(default=None, max_length=160, description="Origin dataset source file")
    min_flow_duration: int | None = Field(default=None, ge=0, description="Minimum flow duration in microseconds")
    max_flow_duration: int | None = Field(default=None, ge=0, description="Maximum flow duration in microseconds")
    
    # Metadata filtering fields (Requirement B4)
    src_ip: str | None = Field(default=None, max_length=45, description="Source IPv4/IPv6 address")
    dst_ip: str | None = Field(default=None, max_length=45, description="Destination IPv4/IPv6 address")
    src_port: int | None = Field(default=None, ge=0, le=65535, description="Source port number")
    dst_port: int | None = Field(default=None, ge=0, le=65535, description="Destination port number")
    start_time: str | None = Field(default=None, description="ISO timestamp start filter")
    end_time: str | None = Field(default=None, description="ISO timestamp end filter")

    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def valid_range(self):
        if (self.min_flow_duration is not None and self.max_flow_duration is not None
                and self.min_flow_duration > self.max_flow_duration):
            raise ValueError("min_flow_duration must not exceed max_flow_duration")
        return self


class IncidentSearchResponse(BaseModel):
    sqlite_matches: list[dict[str, Any]]
    synapt_status: str
    synapt_evidence: list[dict[str, Any]]
    limitations: list[str]


class FlowInvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: int | None = Field(default=None, ge=1, description="Target flow record_id in SQLite")
    query: str | None = Field(default=None, max_length=500, description="Analyst question or alert summary")
    flow_data: dict[str, Any] | None = Field(default=None, description="Optional raw or synthetic flow fields")
    attack_family: str | None = Field(default=None, max_length=100)
    protocol: int | None = Field(default=None, ge=0, le=255)
    limit_similar_flows: int = Field(default=5, ge=1, le=20)

    @model_validator(mode="after")
    def validate_non_empty(self):
        # Reject completely empty requests
        has_id = self.record_id is not None
        has_query = bool(self.query and self.query.strip())
        has_flow = bool(self.flow_data and isinstance(self.flow_data, dict))
        if not (has_id or has_query or has_flow):
            raise ValueError("Investigation request must supply at least a record_id, query text, or flow_data.")
        return self


class FeatureDeviation(BaseModel):
    feature: str
    observed_value: float
    benign_baseline: float
    deviation_magnitude: float


class FlowInvestigationResponse(BaseModel):
    record_id: int | None = None
    predicted_family: str
    confidence: float | None = None
    risk_score: float | None = None
    anomaly_score: float | None = None
    is_anomaly: bool | None = None
    severity: str
    priority_level: str
    feature_attributions: list[FeatureDeviation]
    synapt_analysis: str
    mitre_tactics: list[dict[str, str]]
    investigation_steps: list[str]
    recommended_response: list[str]
    similar_flows: list[dict[str, Any]]
    source_provenance: dict[str, Any]
    guardrail_status: str
    judge_verdict: dict[str, Any] | None = None
    limitations: list[str]


class AnalystFeedbackRequest(BaseModel):
    record_id: int | None = None
    query: str | None = None
    predicted_family: str
    analyst_verdict: Literal["confirmed_malicious", "false_positive", "benign", "needs_escalation"]
    corrected_family: str | None = Field(default=None, description="Analyst-corrected attack family for retraining")
    rating: int = Field(ge=1, le=5)
    notes: str | None = Field(default=None, max_length=1000)


class AnalystFeedbackResponse(BaseModel):
    status: str
    feedback_id: int | None
    synapt_synced: bool
    sync_status: str | None = None
    message: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    record_id: int | None = Field(default=None, description="Optional target flow ID")


class ChatResponse(BaseModel):
    reply: str
    flow_context: dict[str, Any] | None = None
    mitre_tactics: list[dict[str, str]] | None = None
    provenance: dict[str, Any] | None = None
