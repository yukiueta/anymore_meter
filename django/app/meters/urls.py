from django.urls import path
from .views import (
    MeterListView,
    MeterCreateView,
    MeterDetailView,
    MeterUpdateView,
    MeterDeleteView,
    MeterAssignProjectView,
    MeterUnassignProjectView,
)

urlpatterns = [
    path('list/', MeterListView.as_view()),
    path('create/', MeterCreateView.as_view()),
    path('<int:pk>/detail/', MeterDetailView.as_view()),
    path('<int:pk>/update/', MeterUpdateView.as_view()),
    path('<int:pk>/delete/', MeterDeleteView.as_view()),
    path('<int:pk>/assign/project/', MeterAssignProjectView.as_view()),
    path('<int:pk>/unassign/project/', MeterUnassignProjectView.as_view()),
]