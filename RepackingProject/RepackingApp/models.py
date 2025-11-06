import os

import uuid
from django.conf import settings
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

    record_id = models.CharField(max_length=250, unique=True)
    meeting_id = models.CharField(max_length=250)
    datetime_created = models.DateTimeField()
    datetime_stopped = models.DateTimeField()
    type_recording = models.ForeignKey(TypeRecordingModel, on_delete=models.CASCADE)
    url = models.URLField(default='')

    def __str__(self):
        return f"RecordingModel object ({self.record_id})"

    class Meta:
        verbose_name = "Конференция"
        verbose_name_plural = "Конференции"


class OrderRecordingModel(models.Model):
    count = models.PositiveIntegerField()
    count_failed = models.PositiveIntegerField(default=0)
    count_canceled = models.PositiveIntegerField(default=0)
    uuid = models.UUIDField(default=uuid.uuid4)
    user = models.ForeignKey("AccountApp.UserModel", on_delete=models.PROTECT)
    processed = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"


class RecordingTaskIdModel(models.Model):
    STATUS_CHOICES = (
        (1, "Не обработана"),
        (2, "Ожидает"),
        (3, "Обрабатывается"),
        (4, "Завершена"),
        (5, "Загружена"),
        (6, "Неудачно"),
    )

    recording = models.ForeignKey(RecordingModel, on_delete=models.PROTECT,
                                  to_field="record_id")
    task_id = models.CharField(max_length=36,
                               validators=[
                                   MinLengthValidator(36), MaxLengthValidator(36)
                               ], unique=True)
    order = models.ForeignKey(OrderRecordingModel, on_delete=models.PROTECT)
    status = models.PositiveSmallIntegerField(default=1, choices=STATUS_CHOICES)

    class Meta:
        unique_together = (("recording", "task_id"), )

        verbose_name = "Запись обработки"
        verbose_name_plural = "Записи обработки"


class RecodingFileUserModel(models.Model):
    recording_task = models.ForeignKey(RecordingTaskIdModel, to_field="task_id", on_delete=models.CASCADE)
    file = models.FilePathField(path=settings.BASE_DIR)
    datetime_created = models.DateTimeField(auto_now=True)
    file_size = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Файл конферении"
        verbose_name_plural = "Файлы конферений"