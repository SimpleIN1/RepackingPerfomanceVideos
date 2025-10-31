from django.db import models
from django.core.validators import MinLengthValidator, MaxLengthValidator


class TypeRecordingModel(models.Model):
    name = models.CharField(max_length=250, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип конференции"
        verbose_name_plural = "Типы конференций"


class RecordingModel(models.Model):
    STATUS_CHOICES = (
        (1, "Не обработана"),
        (2, "Ожидает"),
        (3, "Обрабатывается"),
        (4, "Завершена"),
        (5, "Загружена"),
        (6, "Неудачно"),
    )

    record_id = models.CharField(max_length=250, unique=True)
    meeting_id = models.CharField(max_length=250)
    datetime_created = models.DateTimeField()
    datetime_stopped = models.DateTimeField()
    type_recording = models.ForeignKey(TypeRecordingModel, on_delete=models.CASCADE)
    status = models.PositiveSmallIntegerField(default=1, choices=STATUS_CHOICES)
    url = models.URLField(default='')

    def __str__(self):
        return f"RecordingModel object ({self.record_id})"

    class Meta:
        verbose_name = "Конференция"
        verbose_name_plural = "Конференции"


class RecordingTaskIdModel(models.Model):
    recording = models.ForeignKey(RecordingModel, on_delete=models.PROTECT,
                                  to_field="record_id")
    task_id = models.CharField(max_length=36,
                               validators=[
                                   MinLengthValidator(36), MaxLengthValidator(36)
                               ])
    user = models.ForeignKey("AccountApp.UserModel", on_delete=models.PROTECT)

    class Meta:
        unique_together = (("recording", "task_id"), )
