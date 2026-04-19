from __future__ import annotations

import csv
import json
import logging
import datetime
from copy import deepcopy

from RepackingApp.services.analytic.user import AnalyticUser, AnalyticAnonymousUser

HEADERS = ["Имя", "Модератор", "Activity score", "Время разговора", "Время с веб-камерой",
           "Сообщений", "Смайликов", "Вариаты ответов", "Поднятых рук", "Вошел", "Вышел",
           "Продолжительность", ]


class DefaultAnalyticConverterUser:

    def __init__(self, user_data, polls):
        self.data = user_data
        self.polls = polls

    @staticmethod
    def timestamp_to_datetime(timestamp_obj: int):
        datetime_obj = datetime.datetime.fromtimestamp(timestamp_obj / 1000.0)
        return datetime_obj

    @staticmethod
    def format_datetime(datetime_obj: datetime.datetime):
        datetime_obj_formatted = datetime_obj.strftime("%d.%m.%Y, %H:%M:%S")
        return datetime_obj_formatted

    def get_name(self):
        raise NotImplementedError(f"Not Implemented")

    def get_moderator(self):
        raise NotImplementedError(f"Not Implemented")

    def get_talk(self):
        raise NotImplementedError(f"Not Implemented")

    def get_webcam(self):
        raise NotImplementedError(f"Not Implemented")

    def get_message(self):
        raise NotImplementedError(f"Not Implemented")

    def get_reaction(self):
        raise NotImplementedError(f"Not Implemented")

    def get_answers(self):
        raise NotImplementedError(f"Not Implemented")

    def get_raise_hand(self):
        raise NotImplementedError(f"Not Implemented")

    def get_left_on(self):
        raise NotImplementedError(f"Not Implemented")

    def get_registered_on(self):
        raise NotImplementedError(f"Not Implemented")

    def get_duration(self):
        raise NotImplementedError(f"Not Implemented")


class DefaultAnalyticConverter:
    analytic_converter_user_class = None

    def __init__(self, data):
        self.data = data
        self.user_data = data["users"]
        self.users = []
        self.headers = deepcopy(HEADERS)

    def get_polls(self):
        polls = [value for _, value in self.data.get("polls").items()]
        return polls

    def update_header_poll_questions(self, polls):
        raise NotImplementedError(f"Not Implemented")

    def get_activity_score(self, user: AnalyticUser, poll_count: int):
        total_score = 0.0

        not_moderator_users = list(filter(lambda x: not x.moderator, self.users))
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

    def calculate_activity_score_user(self, polls):
        for user in self.users:
            if not user.moderator:
                user.activity_score = self.get_activity_score(user, len(polls))
            else:
                user.activity_score = "-"

    def add_anonymous_answers(self, polls):
        logging.info("Add anonymous answers")
        user = AnalyticAnonymousUser(name="Анонимно")
        anonymous_answers = []
        for poll in polls:
            if poll["anonymous"]:
                answer = ",".join(poll["anonymousAnswers"])
                anonymous_answers.append(answer)
            else:
                anonymous_answers.append("")
        user.answers = anonymous_answers

        if anonymous_answers:
            self.users.append(user)

    def execute(self):
        try:
            polls = self.get_polls()

            for key, value in self.user_data.items():
                logging.info("Get analytic_converter_user_class")
                a_user = self.analytic_converter_user_class(value, polls)

                talk, talk_total_time = a_user.get_talk()
                answers, answer_count = a_user.get_answers()
                user = AnalyticUser(
                    name=a_user.get_name(),
                    moderator=a_user.get_moderator(),
                    message_count=a_user.get_message(),
                    reaction_count=a_user.get_reaction(),
                    left_on=a_user.get_left_on(),
                    registered_on=a_user.get_registered_on(),
                    raise_hand_count=a_user.get_raise_hand(),
                    talk=talk,
                    talk_total_time=talk_total_time,
                    webcam=a_user.get_webcam(),
                    answer_count=answer_count,
                    duration=a_user.get_duration(),
                    answers=answers
                )
                self.users.append(user)

            self.calculate_activity_score_user(polls)
            self.add_anonymous_answers(polls)
            self.update_header_poll_questions(polls)
        except Exception as e:
            logging.error(e)
            return

    def save_analytic_data(self, path: str):
        logging.info("Save analytic data")
        try:
            with open(path, 'w') as f:
                writer = csv.writer(f, delimiter=',')
                writer.writerow(self.headers)
                for item in self.users:
                    writer.writerow(item.to_list())
        except Exception as e:
            logging.error(e)
            return
