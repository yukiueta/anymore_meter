from django.urls import path
from .views import (
    ReadingListView,
    ReadingDetailView,
    DailySummaryListView,
    DailySummaryDetailView,
    MonthlySummaryListView,
    MonthlySummaryDetailView,
)

urlpatterns = [
    path('list/', ReadingListView.as_view()),
    path('<int:pk>/detail/', ReadingDetailView.as_view()),
    path('daily/list/', DailySummaryListView.as_view()),
    path('daily/<int:pk>/detail/', DailySummaryDetailView.as_view()),
    path('monthly/list/', MonthlySummaryListView.as_view()),
    path('monthly/<int:pk>/detail/', MonthlySummaryDetailView.as_view()),
]