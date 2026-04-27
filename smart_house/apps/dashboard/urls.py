from django.urls import path

from .views import status_view, summary_api_view

app_name = "dashboard"

urlpatterns = [
    path("", status_view, name="status"),
    path("api/summary/", summary_api_view, name="summary-api"),
]
