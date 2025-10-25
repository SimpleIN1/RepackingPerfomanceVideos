from django.urls import path

from RepackingApp import views


urlpatterns = [
    path("records/", views.RecordingsView.as_view(), name="repacking-records"),

    path("api/records/room/<int:pk>/", views.RecordingsAPIView.as_view(), name="repacking-api-records"),
    path("api/records/process/", views.ProcessRecordingsAPIView.as_view(), name="repacking-api-process-records"),
    path("api/rooms/", views.RoomsAPIView.as_view(), name="repacking-api-rooms"),

    path("downloads/", views.downloads_view, name="repacking-downloads"),
]
