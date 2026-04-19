
import json
import logging
from datetime import datetime, timedelta

from RepackingApp.services.analytic.default_converter import DefaultAnalyticConverterUser, DefaultAnalyticConverter


class AnalyticConverterUserV30(DefaultAnalyticConverterUser):
    def get_name(self):
        return self.data["name"]

    def get_moderator(self):
        return self.data["isModerator"]

    def get_talk(self):
        logging.info("Fetch talk data")
        talk = self.data.get("talk")
        if not talk:
            return "-"

        total_time = talk["totalTime"]
        if total_time:
            talk_formatted = timedelta(seconds=float(f"{str(total_time)[:-3]}"))
        else:
            talk_formatted = "-"

        return talk_formatted, total_time

    def get_webcam(self):
        logging.info("Fetch webcam data")
        if self.data["webcams"]:
            total_webcam = timedelta(seconds=0)
            for webcam in self.data["webcams"]:
                started_on = datetime.fromtimestamp(webcam["startedOn"] / 1000.0)
                stopped_on = datetime.fromtimestamp(webcam["stoppedOn"] / 1000.0)
                total_webcam += (stopped_on - started_on)

            total_webcam_formatted = str(total_webcam).split('.')[0]
        else:
            total_webcam_formatted = "-"

        return total_webcam_formatted

    def get_message(self):
        return self.data["totalOfMessages"]

    def get_reaction(self):
        return len(self.data["reactions"])

    def get_answers(self):
        logging.info("Calculate answers data")
        answers = []

        for poll in self.polls:
            answer = self.data["answers"].get(poll["pollId"])
            if not answer:
                answer = '-'
            answers.append(", ".join(answer))
        return answers, len(self.data["answers"])

    def get_raise_hand(self):
        logging.info("Get raiseHand data")
        return len(self.data["raiseHand"])

    def __get_session_left_registered(self):
        _, value = list(self.data["intIds"].items())[0]
        return value["sessions"][0]

    def get_left_on(self):
        session_left_on = self.__get_session_left_registered()["leftOn"]
        left_on_tmp = self.timestamp_to_datetime(session_left_on)
        left_on = self.format_datetime(left_on_tmp)
        return left_on

    def get_registered_on(self):
        session_registered_on = self.__get_session_left_registered()["registeredOn"]
        registered_on_tmp = self.timestamp_to_datetime(session_registered_on)
        registered_on = self.format_datetime(registered_on_tmp)
        return registered_on

    def get_duration(self):
        session_obj = self.__get_session_left_registered()
        registered_on_tmp = self.timestamp_to_datetime(session_obj["registeredOn"])
        left_on_tmp = self.timestamp_to_datetime(session_obj["leftOn"])
        duration = f"{str(left_on_tmp - registered_on_tmp).split('.')[0]}"
        return duration


class AnalyticConverterV30(DefaultAnalyticConverter):
    analytic_converter_user_class = AnalyticConverterUserV30

    def update_header_poll_questions(self, polls):
        logging.info("Update header poll question 3.0")
        for poll in polls:
            question = self.data["polls"][poll["pollId"]]["question"]
            self.headers.append(question)


def check_analytic_converter_v30(json_data) -> bool:
    data = json_data
    if data.get("other"):
        return True

    users = data.get("users")
    if users:
        _, user_value = list(users.items())[0]
        _, int_ids_value = list(user_value["intIds"].items())[0]

        if int_ids_value.get("sessions"):
            return True

    return False
