from django.db import models


class TypeMeetingModel(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.name


class MeetingModel(models.Model):
    STATUS_CHOICES = (
        (1, "Не обработана"),
        (2, "Ожидает"),
        (3, "Обрабатывается"),
        (4, "Завершена"),
        (5, "Загружена"),
        (6, "Неудачно"),
    )

    record_id = models.CharField(max_length=250)
    meeting_id = models.CharField(max_length=250)
    datetime_created = models.DateTimeField()
    datetime_stopped = models.DateTimeField()
    type_meeting = models.ForeignKey(TypeMeetingModel, on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(default=1, choices=STATUS_CHOICES)
    url = models.URLField(default='')

    def __str__(self):
        return f"MeetingModel object ({self.record_id})"

    class Meta:
        unique_together = ("record_id", "meeting_id")
