import os

from django.contrib import admin

from RepackingApp.models import TypeRecordingModel, RecordingModel, RecordingTaskIdModel, RecodingFileUserModel


@admin.register(TypeRecordingModel)
class TypeRecordingModelAdmin(admin.ModelAdmin):
    list_display = ("name", )


@admin.action(description="Перевести в статус 'Не обработана'")
def to_draft_status(modeladmin, request, queryset):
    queryset.update(status=1)


@admin.register(RecordingModel)
class RecordingModelAdmin(admin.ModelAdmin):
    list_filter = ("status", "type_recording", )
    list_display = ("record_id", "meeting_id", "datetime_created", "datetime_stopped", "status", )
    search_fields = ("record_id", )
    actions = [
        to_draft_status,
    ]


@admin.register(RecordingTaskIdModel)
class RecordingTaskIdModelAdmin(admin.ModelAdmin):
    list_display = ("recording", "task_id", "user")


@admin.register(RecodingFileUserModel)
class RecodingFileUserModelAdmin(admin.ModelAdmin):
    list_display = ("recording", "user", "file", "datetime_created")

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            os.remove(obj.file)
            obj.delete()
