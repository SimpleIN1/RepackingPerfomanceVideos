import os

from django.contrib import admin

from RepackingApp.models import TypeRecordingModel, RecordingModel, RecordingTaskIdModel, RecodingFileUserModel, \
    OrderRecordingModel


@admin.action(description="Перевести в статус 'Не обработана'")
def to_draft_status(modeladmin, request, queryset):
    queryset.update(status=1)


@admin.action(description="Перевести в статус 'Завершена'")
def to_compete_status(modeladmin, request, queryset):
    queryset.update(status=4)


@admin.register(TypeRecordingModel)
class TypeRecordingModelAdmin(admin.ModelAdmin):
    list_display = ("name", )


@admin.register(RecordingModel)
class RecordingModelAdmin(admin.ModelAdmin):
    list_filter = ("type_recording", )
    list_display = ("record_id", "meeting_id", "datetime_created", "datetime_stopped", )
    search_fields = ("record_id", )


@admin.register(RecordingTaskIdModel)
class RecordingTaskIdModelAdmin(admin.ModelAdmin):
    list_display = ("recording", "task_id", "order", "status",)
    list_filter = ("status", )
    actions = [
        to_draft_status,
        to_compete_status
    ]


@admin.register(RecodingFileUserModel)
class RecodingFileUserModelAdmin(admin.ModelAdmin):
    list_display = ("file", "file_size", "datetime_created", )

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if os.path.exists(obj.file):
                os.remove(obj.file)
            obj.delete()


@admin.register(OrderRecordingModel)
class OrderRecordingModelAdmin(admin.ModelAdmin):
    list_display = ("id", "count", "count_failed", "count_canceled", "uuid", "user", "processed")
    list_filter = ("processed", )

    def has_change_permission(self, request, obj=None):
        return False
