from django.urls import path
from .views import (
    KeyListView,
    KeyCreateView,
    KeyDetailView,
    KeyUpdateView,
    KeyRevealView,
    KeyRegenerateView,
    KeyBulkImportView,
)

urlpatterns = [
    path('list/', KeyListView.as_view()),
    path('create/', KeyCreateView.as_view()),
    path('<int:pk>/detail/', KeyDetailView.as_view()),
    path('<int:pk>/update/', KeyUpdateView.as_view()),
    path('<int:pk>/reveal/', KeyRevealView.as_view()),
    path('<int:pk>/regenerate/', KeyRegenerateView.as_view()),
    path('bulk/import/', KeyBulkImportView.as_view()),
]