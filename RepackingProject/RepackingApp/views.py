import json
from http import HTTPStatus

# from django.views import View
from django.views.generic import View
from django.shortcuts import render
from django.core import serializers
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.contrib.auth.mixins import LoginRequiredMixin

from RepackingApp import forms
from RepackingApp.models import MeetingModel
from RepackingApp.services.records import get_type_recordings, get_recordings, get_recordings_to_dict, \
    get_type_recordings_to_dict


class RecordingsView(View):
    template_name = "repacking/records.html"

    def get(self, request):
        context = {}

        type_recordings = get_type_recordings()
        context["type_recordings"] = type_recordings
        context["status_list"] = MeetingModel.STATUS_CHOICES

        return render(request, self.template_name, context=context)


class RecordingsAPIView(LoginRequiredMixin, View):

    def get(self, request, pk):

        recordings = get_recordings_to_dict(
            fields=["record_id", "datetime_created", "datetime_stopped", "status", "url"],
            type_meeting__id=pk
        )

        return HttpResponse(
            json.dumps({
                "success": True,
                "recordings": [item for item in recordings]
            }, default=str),
            content_type='application/json',
            status=HTTPStatus.OK
        )


class ProcessRecordingsAPIView(View):
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


def records_view(request):

    return render(request, "repacking/records.html", context={})


def downloads_view(request):
    return render(request, "repacking/downloads.html", context={})
