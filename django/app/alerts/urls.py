from django.urls import path
from .views import (
    AlertListView,
    AlertDetailView,
    AlertAcknowledgeView,
    AlertResolveView,
    AlertUpdateNoteView,
)

urlpatterns = [
    path('list/', AlertListView.as_view()),
    path('<int:pk>/detail/', AlertDetailView.as_view()),
    path('<int:pk>/acknowledge/', AlertAcknowledgeView.as_view()),
    path('<int:pk>/resolve/', AlertResolveView.as_view()),
    path('<int:pk>/update_note/', AlertUpdateNoteView.as_view()),
]