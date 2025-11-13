
class EmailUser:
    def __init__(self, user, session, kind, api_call, callback, **data):
        self.user = user
        self.session = session
        self.kind = kind
        self.api_call = api_call
        self.callback = callback
        self.data = data


class NotifyEmailUser(EmailUser):
    def __init__(self, video_count, video_count_failed, video_count_cancelled, type_name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.video_count = video_count
        self.video_count_failed = video_count_failed
        self.video_count_cancelled = video_count_cancelled
        self.type_name = type_name


class ConfirmationEmailUser(EmailUser):
    pass
