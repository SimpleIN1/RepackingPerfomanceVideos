from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalyticUser:
    name: str
    moderator: bool
    talk: str
    webcam: str
    registered_on: str
    left_on: str
    duration: str
    talk_total_time: int = -1
    message_count: int = -1
    reaction_count: int = -1
    answer_count: int = -1
    raise_hand_count: int = -1
    answers: list | None = None
    activity_score: float | None = None

    def to_list(self) -> list:
        tmp = [
            self.name, self.moderator, self.activity_score, self.talk, self.webcam,
            self.message_count, self.reaction_count, self.answer_count, self.raise_hand_count,
            self.registered_on, self.left_on, self.duration]
        if self.answers:
            tmp.extend(self.answers)
        return tmp


@dataclass
class AnalyticAnonymousUser(AnalyticUser):
    moderator: str = ""
    talk: str = ""
    webcam: str = ""
    registered_on: str = ""
    left_on: str = ""
    duration: str = ""
    talk_total_time: str = ""
    message_count: str = ""
    reaction_count: str = ""
    answer_count: str = ""
    raise_hand_count: str = ""
    activity_score: str = ""
