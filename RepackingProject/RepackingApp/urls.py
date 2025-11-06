from django.urls import path

from RepackingApp import views


urlpatterns = [
    path("records/", views.RecordingsView.as_view(), name="repacking-records"),

    path("api/records/room/<int:pk>/", views.RecordingsAPIView.as_view(), name="repacking-api-records"),
    path("api/records/room/<int:pk>/status/", views.RecordingsStatusAPIView.as_view(), name="repacking-api-records-status"),
    path("api/records/process/", views.ProcessRecordingsAPIView.as_view(), name="repacking-api-process-records"),
    path("api/records/terminate/", views.TerminateRecordingsAPIView.as_view(), name="repacking-api-terminate-records"),
    path("api/records/upload/", views.UploadRecordingsAPIView.as_view(), name="repacking-api-upload-records"),
    path("api/rooms/", views.RoomsAPIView.as_view(), name="repacking-api-rooms"),

    path("download/", views.DownloadView.as_view(), name="repacking-downloads"),
    path("download/<int:id>/", views.DownloadFileView.as_view(), name="repacking-downloads-id"),
]
