from django.urls import path

from RepackingApp import views

urlpatterns = [
    path("records/room/<int:pk>/", views.RecordingsAPIView.as_view(), name="repacking-api-records"),
    path("records/room/<int:pk>/status/", views.RecordingsStatusAPIView.as_view(), name="repacking-api-records-status"),
    path("records/process/", views.ProcessRecordingsAPIView.as_view(), name="repacking-api-process-records"),
    path("records/terminate/", views.TerminateRecordingsAPIView.as_view(), name="repacking-api-terminate-records"),
    path("records/upload/", views.UploadRecordingsAPIView.as_view(), name="repacking-api-upload-records"),

    path("rooms/", views.RoomsAPIView.as_view(), name="repacking-api-rooms"),

    path("callback/analytics", views.AnalyticsCallbackAPIView.as_view(), name="analytics-callback"),

    path("download/<int:id>/", views.DownloadFileView.as_view(), name="repacking-downloads-id"),
]
