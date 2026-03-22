from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class InterviewConfig:
    silence_threshold_seconds: float = 1.2
    min_round_seconds: float = 2.0
    followup_score_threshold: float = 0.7
    clarity_threshold: float = 0.7
    confidence_threshold: float = 0.6
    max_followups_per_question: int = 2


@dataclass
class RoundInput:
    question_id: str
    question_text: str
    answer_audio_path: str
    answer_duration_seconds: float
    silence_tail_seconds: float


@dataclass
class SemanticEvaluation:
    correctness_score: float
    clarity_score: float
    reasoning: str
    suggested_followup_focus: Optional[str] = None


@dataclass
class EmotionEvaluation:
    confidence_score: float
    speech_rate_wpm: float
    emotion_label: str
    prosody_comment: str


@dataclass
class FollowUpDecision:
    should_follow_up: bool
    follow_up_question: Optional[str]
    reason: str


@dataclass
class RoundResult:
    question_id: str
    question_text: str
    transcript: str
    semantic: SemanticEvaluation
    emotion: EmotionEvaluation
    follow_up: FollowUpDecision


@dataclass
class InterviewContext:
    candidate_id: str
    rounds: List[RoundResult] = field(default_factory=list)
    followup_count_by_question: Dict[str, int] = field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class FinalReport:
    candidate_id: str
    semantic_avg: float
    clarity_avg: float
    confidence_avg: float
    strengths: List[str]
    improvements: List[str]
    recommendations: List[str]
