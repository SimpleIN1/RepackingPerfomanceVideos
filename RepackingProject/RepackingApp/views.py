import os
import json
import random
from http import HTTPStatus
from urllib.parse import urlsplit

from django.db.models import Q
from django.conf import settings
from django.shortcuts import render, redirect
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.contrib.sessions.models import Session
from django.http import HttpResponse, FileResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from CeleryApp.app import app
from CeleryApp.tasks import repack_threads_video_task, remove_dirs_task, \
    upload_processed_records, terminate_process_task
from RepackingApp import forms
from RepackingApp.models import RecordingModel, RecordingTaskIdModel, RecodingFileUserModel
from RepackingApp.services.downloads import get_recording_files, get_download_recording_files, \
    get_recording_files_for_upload
from RepackingApp.services.order_record import create_recording_order
from RepackingApp.services.record_task import create_recording_task, delete_recordings_tasks, get_recording_tasks, \
    create_recording_tasks, update_recording_tasks, get_recording_tasks_status, \
    get_recording_tasks_left_outer_recording, get_recording_order_tasks, get_recording_order_tasks_distinct_record
from RepackingApp.services.records import get_type_recordings, \
    get_recordings_to_dict, \
    get_type_recordings_to_dict, get_recordings_foreinkey_type_recording, get_recordings
from common.redis_conn import get_redis_connection


class RecordingsView(LoginRequiredMixin, View):
    template_name = "repacking/records.html"

    @method_decorator(cache_page(60 * 60 * 12), name='dispatch')
    def get(self, request):
        context = {}
        context["status_list"] = RecordingTaskIdModel.STATUS_CHOICES

        return render(request, self.template_name, context=context)


class RecordingsAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):

        key = settings.CACHE_PK_RECORDINGS.format(pk)
        recordings = cache.get(key)
        if not recordings:
            queryset = get_recordings_to_dict(
                fields=["record_id", "datetime_created", "datetime_stopped", "url"],
                filter_query=Q(type_recording__id=pk)
            )
            recordings = [item for item in queryset]
            cache.set(key, recordings, 60 * 60 * 24)

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": recordings
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class RecordingsStatusAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):
        recording_task_d = get_recording_tasks_status(request.user.id, pk)

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": [recording_task_d[item] for item in recording_task_d]
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class ProcessRecordingsAPIView(LoginRequiredMixin, View):
    form_class = forms.ProcessRecordingsForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}

        form = self.form_class(request.POST)

        if not form.is_valid():
            return HttpResponse(
                json.dumps({
                    "success": False,
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        recording_ids = form.cleaned_data["recording_ids"].split(',')

        recording_tasks = get_recording_order_tasks_distinct_record(
            Q(recording_id__in=recording_ids) & Q(order__user_id=request.user.id) & Q(status__in=[2, 3])
        )
        rids = [item.recording_id for item in recording_tasks]
        clean_recording_ids = list(set(recording_ids).difference(rids))
        recordings = get_recordings(Q(record_id__in=clean_recording_ids)).only("record_id", "type_recording_id", "url")

        if not recordings:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "error", "title": "Обработка",
                        "text": f"Записи не найдены или уже находятся в обработке"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        order = create_recording_order(count=len(clean_recording_ids), user_id=request.user.id,
                                       type_recording_id=recordings[0].type_recording_id)

        for recording in recordings:
            resource = urlsplit(recording.url).netloc

            task_params = {
                "resource": resource,
                "user_id": request.user.id,
                "recording_task": {
                    "recording_id": recording.record_id,
                    "task_id": None,
                    "order_id": order.id,
                    "status": 2,
                }
            }
            repack_threads_video_task.delay(**task_params)

        recordings = [
            {"record_id": recording_id, "status": 2}
            for recording_id in clean_recording_ids
        ]

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": recordings
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class TerminateRecordingsAPIView(LoginRequiredMixin, View):
    form_class = forms.ProcessRecordingsForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}

        form = self.form_class(request.POST)

        if not form.is_valid():
            return HttpResponse(
                json.dumps({
                    "success": False,
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        context["recording_ids"] = form.cleaned_data["recording_ids"].split(',')

        clean_recording_tasks = get_recording_tasks(
            Q(recording_id__in=context["recording_ids"]) & Q(order__user_id=request.user.id)
            & Q(status__in=[2, 3])
        )

        clean_recording_tasks_ids = [
            recording_task.recording_id for recording_task in clean_recording_tasks
        ]

        if not clean_recording_tasks:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "warning", "title": "Завершение",
                        "text": f"Записи, которые поставлены в очередь на обработку или обрабатываются не найдены"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )
        with get_redis_connection() as r:
            for recording_task in clean_recording_tasks:
                r.incr(settings.REDIS_KEY_ORDER_CANCELLED.format(recording_task.order_id))

        tasks = [recording_task.task_id for recording_task in clean_recording_tasks]
        app.control.revoke(tasks, terminate=True, signal='SIGKILL')
        terminate_process_task.delay(tasks)

        # delete_recordings_tasks(Q(task_id__in=tasks))
        update_recording_tasks(
            Q(task_id__in=tasks), status=1
        )

        return HttpResponse(
            json.dumps({
                "success": True,
                "recording_ids": clean_recording_tasks_ids
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class UploadRecordingsAPIView(LoginRequiredMixin, View):
    form_class = forms.ProcessRecordingsForm

    @method_decorator(csrf_protect)
    def post(self, request):
        context = {}

        if not request.user.nextcloud_upload:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "warning", "title": "Загрузка",
                        "text": f"У вас нет доступа на загрузку записей в NextCloud"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        form = self.form_class(request.POST)

        if not form.is_valid():
            return HttpResponse(
                json.dumps({
                    "success": False,
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.BAD_REQUEST
            )

        recording_ids = form.cleaned_data["recording_ids"].split(',')

        recording_files_d = get_recording_files_for_upload(
            Q(recording_task__recording_id__in=recording_ids) & Q(recording_task__status=4)
        )

        if not recording_files_d:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "error", "title": "404", "text": f"Записи не найдены"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        for key, rfv in recording_files_d.items():
            upload_processed_records.delay(rfv.recording_task_id,
                                           request.user.id,
                                           rfv.recording_task.recording.type_recording.name,
                                           rfv.file)

        return HttpResponse(
            json.dumps({
                "success": True
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class RoomsAPIView(LoginRequiredMixin, View):

    def get(self, request):
        type_recordings = cache.get(settings.CACHE_TYPE_RECORDINGS)
        if not type_recordings:
            queryset = get_type_recordings_to_dict(["id", "name"])
            type_recordings = [item for item in queryset]
            cache.set(settings.CACHE_TYPE_RECORDINGS, type_recordings)

        return HttpResponse(
            json.dumps({
                "success": True,
                "rooms": type_recordings
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class DownloadView(LoginRequiredMixin, View):
    template_name = "repacking/downloads.html"

    def get(self, request):
        context = {}

        session_id = request.GET.get("session_id")
        if session_id:
            try:
                session_id_db = Session.objects.get(pk=session_id)
                if session_id_db:
                    request.session.session_key = session_id
            except Session.DoesNotExist:
                return redirect("not_found")

            user_id = request.session.get('_auth_user_id')
            if not user_id:
                return redirect("not_found")

        else:
            user_id = request.user.id

        recording_files = get_download_recording_files(Q(recording_task__order__user_id=user_id))
        context["rfiles"] = recording_files
        return render(request, self.template_name, context=context)


class DownloadFileView(LoginRequiredMixin, View):
    def get(self, request, id):
        rfile = get_object_or_404(RecodingFileUserModel, pk=id)

        if not os.path.exists(rfile.file):
            return redirect("not-found")

        return FileResponse(open(rfile.file, "rb"))


class TestAPIView(View):

    def get(self, request):

        return HttpResponse(
            json.dumps({
                "success": False,
                "recordings": {f"test{i}": f"value{i}" for i in range(random.randint(10, 100), random.randint(140, 10000))}
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )
