from __future__ import annotations

import csv
import json
import logging
import datetime
from dataclasses import dataclass


@dataclass
class AnalyticUser:
    name: str
    moderator: bool
    talk: str
    talk_total_time: int
    webcam: str
    message_count: int
    reaction_count: int
    answer_count: int
    raise_hand_count: int
    registered_on: str
    left_on: str
    duration: str
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


headers = ["Имя", "Модератор", "Activity score", "Время разговора", "Время с веб-камерой",
           "Сообщений", "Смайликов", "Вариаты ответов", "Поднятых рук", "Вошел", "Вышел",
           "Продолжительность", ]


def timestamp_to_datetime(timestamp_obj: int):
    datetime_obj = datetime.datetime.fromtimestamp(timestamp_obj/1000.0)
    return datetime_obj


def format_datetime(datetime_obj: datetime.datetime):
    datetime_obj_formatted = datetime_obj.strftime("%d.%m.%Y, %H:%M:%S")
    return datetime_obj_formatted


def get_webcam(data):
    logging.info("Fetch webcam data")
    if data["webcams"]:
        total_webcam = datetime.timedelta(seconds=0)
        for webcam in data["webcams"]:
            started_on = datetime.datetime.fromtimestamp(webcam["started_on"]/1000.0)
            stopped_on = datetime.datetime.fromtimestamp(webcam["stopped_on"]/1000.0)
            total_webcam += (stopped_on - started_on)

        total_webcam_formatted = str(total_webcam).split('.')[0]
    else:
        total_webcam_formatted = "-"

    return total_webcam_formatted


def get_talk(data):
    logging.info("Fetch talk data")
    talk = data.get("talk")
    if not talk:
        return "-"

    total_time = talk["total_time"]
    if total_time:
        talk_formatted = datetime.timedelta(seconds=float(f"{str(total_time)[:-3]}"))
    else:
        talk_formatted = "-"

    return talk_formatted, total_time


def get_raise_hand(data):
    logging.info("Calculate raiseHand data")
    count = 0
    for emoji in data["emojis"]:
        if emoji["name"] == "raiseHand":
            count += 1
    return count


def get_answers(data, polls):
    logging.info("Calculate answers data")
    answers = []

    for poll in polls:
        answer = data["answers"].get(poll)
        if not answer:
            answer = '-'
        answers.append(", ".join(answer))
    return answers, len(data["answers"])


def update_header_poll_questions(data, polls, headers):
    for poll in polls:
        question = data["polls"][poll]["question"]
        headers.append(question)


def get_activity_score(user, users, poll_count):
    total_score = 0.0

    not_moderator_users = list(filter(lambda x: not x.moderator, users))
    max_talk_total_time = max(not_moderator_users, key=lambda x: x.talk_total_time).talk_total_time
    if max_talk_total_time > 0:
        total_score += user.talk_total_time / max_talk_total_time * 2

    max_message_count = max(not_moderator_users, key=lambda x: x.message_count).message_count
    if max_message_count > 0:
        total_score += user.message_count / max_message_count * 2

    max_raise_hand_count = max(not_moderator_users, key=lambda x: x.raise_hand_count).raise_hand_count
    if max_raise_hand_count > 0:
        total_score += user.raise_hand_count / max_raise_hand_count * 2

    max_reaction_count = max(not_moderator_users, key=lambda x: x.reaction_count).reaction_count
    if max_reaction_count > 0:
        total_score += user.reaction_count / max_reaction_count * 2

    if poll_count > 0:
        total_score += user.answer_count / poll_count * 2

    return round(total_score, 1)


def save_analytic_data(path, headers: list, items: list[AnalyticUser]):
    with open(path, 'w') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(headers)
        for item in items:
            writer.writerow(item.to_list())


def covert_bbb_analytic_json_data(json_data, path_save):
    try:
        logging.info("Convert analytic data")
        data = json_data.get("data")

        if not data:
            logging.error("data is empty")

        polls = polls_tmp.keys() if (polls_tmp := data.get("polls")) else []

        logging.info("Fetching users from json")
        users = []
        for key, value in data["users"].items():
            moderator = value["isModerator"]
            name = value["name"]
            message_count = value["totalOfMessages"]
            reaction_count = len(value["reactions"])
            ext_id = value["extId"]

            left_on = timestamp_to_datetime(value["intIds"][ext_id]["leftOn"])
            left_on_formatted = format_datetime(left_on)
            registered_on = timestamp_to_datetime(value["intIds"][ext_id]["registeredOn"])
            registered_on_formatted = format_datetime(registered_on)
            duration = f"{str(left_on - registered_on).split('.')[0]}"

            talk, talk_total_time = get_talk(value)
            webcam = get_webcam(value)
            raise_hand_count = get_raise_hand(value)
            answers, len_answers = get_answers(value, polls)

            user = AnalyticUser(
                name=name,
                moderator=moderator,
                message_count=message_count,
                reaction_count=reaction_count,
                left_on=left_on_formatted,
                registered_on=registered_on_formatted,
                raise_hand_count=raise_hand_count,
                talk=talk,
                talk_total_time=talk_total_time,
                webcam=webcam,
                answer_count=len_answers,
                duration=duration,
                answers=answers
            )
            users.append(user)

        logging.info("Calculate activity score for users")
        for user in users:
            if not user.moderator:
                user.activity_score = get_activity_score(user, users, len(polls))
            else:
                user.activity_score = "-"

        update_header_poll_questions(data, polls, headers)
        logging.info("Save analytic data")

        save_analytic_data(path_save, headers, users)
        return path_save
    except Exception as e:
        logging.error(e)
        return None


if __name__ == '__main__':
    path = "../../analytic_test-b397ec14dc3e9eef3e73fd0f5800af12afe8e8bb-1775124240464.json"
    path_save = "analytic_test.csv"
    with open(path) as f:
        json_data = json.load(f)
        covert_bbb_analytic_json_data(json_data, path_save)
