from datetime import datetime, timezone, timedelta

from django.conf import settings

from common.manage_datetime import is_expiration_time


class SessionService:
    _session = None

    @property
    def session(self):
        return self._session

    @session.setter
    def session(self, data):
        self._session = data


class UserSession:
    def __init__(self, user, session):
        self.user = user
        self.session = session


class ConfirmationCodeSessionService:
    def __init__(self, session, user=None):
        self.session = session
        self.user = user

        session_code = self.session.get(settings.CONFIRMATION_CODE_SESSION)

        if session_code is None:
            session_code = self.session[settings.CONFIRMATION_CODE_SESSION] = {}

        self.session_code = session_code

    def save(self):
        self.session[settings.CONFIRMATION_CODE_SESSION] = self.session_code
        self.session.modified = True

    def clear(self):
        del self.session[settings.CONFIRMATION_CODE_SESSION]
        self.save()

    def clear_kind(self, kind):
        if self.session_code.get(kind):
            del self.session_code[kind]
            self.save()

    def check(self, code, kind):

        if not self.session_code.get(kind):
            return False

        if self.get_attempt(kind) > settings.SUCCESS_ATTEMPT_COUNT:
            return False

        confirmation_email = self.session_code[kind].get("confirmation_email")

        if confirmation_email:
            return False

        if not self.is_active_code(kind):
            self.clear_kind(kind)
            return False

        if not code == self.session_code[kind]["code"]:
            return False

        return True

    def check_kind(self, kind):
        return self.session_code.get(kind)

    def is_active_code(self, kind):
        datetime_created = self.session_code[kind].get("datetime_created")

        if not datetime_created:
            return False

        return is_expiration_time(datetime_created, settings.EXPIRATION_MINUTES)

    def add(self, code, kind, *args, **data):
        self.session_code.setdefault(kind, {})
        self.session_code[kind]["code"] = code
        self.session_code[kind]["confirmation_email"] = False
        self.session_code[kind]["datetime_created"] = str(datetime.now().timestamp()).split('.')[0]

        if self.user:
            self.session_code[kind]["user_id"] = self.user.id

        self.session_code[kind]["data"] = data
        self.save()

    def get_user_id(self, kind):
        if not self.session_code.get(kind):
            return None
        return self.session_code[kind]["user_id"]

    def get_data(self, kind):
        return self.session_code[kind]["data"]

    def get_full_data(self):
        return {settings.CONFIRMATION_CODE_SESSION: self.session_code}

    def confirm_code(self, kind):
        self.session_code.setdefault(kind, {})
        self.session_code[kind]["confirmation_email"] = True
        self.save()

    def check_confirm(self, kind):
        try:
            if not self.session_code[kind]["confirmation_email"] or not self.is_active_code(kind):
                return False

            return True

        except KeyError:
            return False

    def increase_attempt(self, kind):
        attempt = self.session_code[kind].get("attempt") or 0
        self.session_code[kind]["attempt"] = attempt+1
        self.save()

    def get_attempt(self, kind):
        attempt = self.session_code[kind].get("attempt") or 0
        return attempt

    def reset_attempt(self, kind):
        self.session_code[kind]["attempt"] = 0
        self.save()


class NotifySessionService:
    def __init__(self, session):
        self.session = session

        session_notify = self.session.get(settings.NOTIFY_CODE_SESSION)

        if session_notify is None:
            session_notify = self.session[settings.NOTIFY_CODE_SESSION] = {}

        self.session_notify = session_notify

    def is_active(self):
        datetime_created = self.session_notify.get("datetime_created")

        if not datetime_created:
            return False

        return is_expiration_time(datetime_created, settings.NOTIFY_EXPIRATION_MINUTES)

    def get_full_data(self):
        return {settings.NOTIFY_CODE_SESSION: self.session_notify}

    def get_user_id(self):
        user_id = self.session_notify.get("user_id")
        return user_id
