import json
import os
import signal
import redis
from http import HTTPStatus
from urllib.parse import urlsplit

from django.db.models import Q
from django.shortcuts import render
from django.core.cache import cache
from django.http import HttpResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from CeleryApp.app import app
from CeleryApp.tasks import repack_threads_video_task, repack_threads_video_task
from RepackingApp import forms
from RepackingApp.models import RecordingModel, RecordingTaskIdModel
from RepackingApp.services.record_task import create_recording_task, delete_recordings_tasks, get_recording_tasks, \
    create_recording_tasks
from RepackingApp.services.records import get_type_recordings, get_recordings_foreinkey_type_recording, \
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
        context["status_list"] = RecordingModel.STATUS_CHOICES

        return render(request, self.template_name, context=context)


class RecordingsAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):

        recordings = get_recordings_to_dict(
            fields=["record_id", "datetime_created", "datetime_stopped", "status", "url"],
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
                        "type": "error", "title": "404", "text": f"Записи не найдена"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        clean_recording_ids = [recordings.record_id for recordings in recordings]

        update_recordings(Q(record_id__in=clean_recording_ids), status=2)

        recording_task_list = []
        for recording in recordings:
            resource = urlsplit(recording.url).netloc

            task = repack_threads_video_task.delay(resource=resource,
                                                   recording_id=recording.record_id)

            recording_task_list.append(
                RecordingTaskIdModel(recording=recording, task_id=task, user=request.user)
            )

        create_recording_tasks(recording_task_list)

        recordings = get_recordings_to_dict(
            fields=["record_id", "status"],
            filter_query=Q(record_id__in=clean_recording_ids)
        )

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": [item for item in recordings]
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

        clean_recording_tasks = get_recording_tasks(Q(recording_id__in=context["recording_ids"]) & Q(user=request.user))
        clean_recording_tasks_ids = [
            recording_task.recording_id for recording_task in clean_recording_tasks
        ]

        if not clean_recording_tasks:
            return HttpResponse(
                json.dumps({
                    "success": False,
                    "message": {
                        "type": "error", "title": "404",
                        "text": f"Записи не найдена"
                    },
                }, default=str),
                content_type='application/json',
                status=HTTPStatus.OK
            )

        if clean_recording_tasks:
            tasks = [recording_task.task_id for recording_task in clean_recording_tasks]

            with get_redis_connection() as r:

                app.control.revoke(tasks, terminate=True, signal='SIGKILL')

                for recording_task in clean_recording_tasks:
                    pid = r.get(recording_task.task_id)
                    r.delete(recording_task.task_id)
                    if pid:
                        terminate_process(pid.decode('utf-8'))

            delete_recordings_tasks(Q(recording_id__in=clean_recording_tasks_ids))
            update_recordings(Q(record_id__in=clean_recording_tasks_ids), status=1)

        return HttpResponse(
            json.dumps({
                "success": True,
                "recording_ids": form.cleaned_data["recording_ids"].split(',')
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


def downloads_view(request):
    return render(request, "repacking/downloads.html", context={})
