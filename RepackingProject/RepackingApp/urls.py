from django.urls import path

from RepackingApp import views

api_route = "api/repacking"

urlpatterns = [
    path("records/", views.RecordingsView.as_view(), name="repacking-records"),
    path("download/", views.DownloadView.as_view(), name="repacking-downloads"),
]
