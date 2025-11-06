import json
import os
import signal
import redis
import pytz
from http import HTTPStatus
from urllib.parse import urlsplit

import uuid
from django.db.models import Q
from django.conf import settings
from django.shortcuts import render
from django.core.cache import cache
from django.views.generic import View
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, FileResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from CeleryApp.app import app
from CeleryApp.tasks import repack_threads_video_task, repack_threads_video_task, remove_dirs_task, \
    upload_processed_records
from RepackingApp import forms
from RepackingApp.models import RecordingModel, RecordingTaskIdModel, RecodingFileUserModel
from RepackingApp.services.downloads import get_recording_files, get_download_recording_files, \
    get_recording_files_for_upload
from RepackingApp.services.order_record import create_recording_order
from RepackingApp.services.record_task import create_recording_task, delete_recordings_tasks, get_recording_tasks, \
    create_recording_tasks, update_recording_tasks, get_recording_tasks_status
from RepackingApp.services.records import get_type_recordings, \
    get_recordings_to_dict, \
    get_type_recordings_to_dict, get_recording, get_recordings, update_recordings
from common.process_termination import terminate_process
from common.redis_conn import get_redis_connection


class RecordingsView(LoginRequiredMixin, View):
    template_name = "repacking/records.html"

    def get(self, request):
        context = {}

        type_recordings = get_type_recordings()
        context["type_recordings"] = type_recordings
        context["status_list"] = RecordingTaskIdModel.STATUS_CHOICES

        return render(request, self.template_name, context=context)


class RecordingsAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):
        recordings = get_recordings_to_dict(
            fields=["record_id", "datetime_created", "datetime_stopped", "url"],
            filter_query=Q(type_recording__id=pk)
        )
        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": [item for item in recordings]
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class RecordingsStatusAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):
        recordings = get_recording_tasks_status(request.user.id, pk)

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": [item for item in recordings]
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

        recordings = get_recordings(Q(record_id__in=recording_ids))

        if not recordings:
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

        clean_recording_ids = [recordings.record_id for recordings in recordings]

        order = create_recording_order(count=len(clean_recording_ids), user_id=request.user.id)

        recording_task_list = []
        for recording in recordings:
            resource = urlsplit(recording.url).netloc

            task = repack_threads_video_task.delay(resource=resource,
                                                   type_recording_id=recordings[0].type_recording_id,
                                                   recording_id=recording.record_id,
                                                   user_id=request.user.id,
                                                   order_id=order.id,
                                                   order_count=order.count)
            recording_task_list.append(
                RecordingTaskIdModel(recording=recording, task_id=task, order=order, status=2)
            )

        create_recording_tasks(recording_task_list)

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
        )

        clean_recording_tasks_ids = [
            recording_task.recording_id for recording_task in clean_recording_tasks
        ]

        if not clean_recording_tasks:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "error", "title": "404",
                        "text": f"Записи не найдены"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        if clean_recording_tasks:
            tasks = [recording_task.task_id for recording_task in clean_recording_tasks]

            with get_redis_connection() as r:

                app.control.revoke(tasks, terminate=True, signal='SIGKILL')

                dirnames = []
                for task_id in tasks:
                    process_name = r.get(task_id)
                    r.delete(task_id)
                    if process_name:
                        process_name = process_name.decode('utf-8')
                        terminate_process(process_name)
                        dirnames.append(process_name)

                if dirnames:
                    remove_dirs_task.delay(dirnames)

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

        recording_files = get_recording_files_for_upload(
            Q(recording_task__recording_id__in=recording_ids) & Q(recording_task__status=4)
        )

        if not recording_files:
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

        for recording in recording_files:
            upload_processed_records.delay(recording.recording_task_id,
                                           request.user.id,
                                           recording.recording_task.recording.type_recording.name,
                                           recording.file)

        return HttpResponse(
            json.dumps({
                "success": True
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class RoomsAPIView(LoginRequiredMixin, View):

    def get(self, request):
        recordings = get_type_recordings_to_dict()

        return HttpResponse(
            json.dumps({
                "success": True,
                "rooms": [item for item in recordings]
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class DownloadView(LoginRequiredMixin, View):
    template_name = "repacking/downloads.html"

    def get(self, request):
        context = {}

        recording_files = get_download_recording_files(Q(recording_task__order__user_id=self.request.user.id))
        context["rfiles"] = recording_files
        return render(request, self.template_name, context=context)


class DownloadFileView(LoginRequiredMixin, View):
    def get(self, request, id):
        rfile = get_object_or_404(RecodingFileUserModel, pk=id)
        return FileResponse(open(rfile.file, "rb"))
