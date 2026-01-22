from django.urls import path
from .views import (
    ReadingListView,
    ReadingDetailView,
    ReadingExportView,
    EventListView,
    EventDetailView,
    DailySummaryListView,
    DailySummaryDetailView,
    DailySummaryExportView,
    MonthlySummaryListView,
    MonthlySummaryDetailView,
    MonthlySummaryExportView,
    DailySummaryChartView,
    MonthlySummaryChartView,
)

urlpatterns = [
    # 30分データ
    path('list/', ReadingListView.as_view()),
    path('export/', ReadingExportView.as_view()),
    path('<int:pk>/detail/', ReadingDetailView.as_view()),
    
    # イベントログ
    path('events/list/', EventListView.as_view()),
    path('events/<int:pk>/detail/', EventDetailView.as_view()),
    
    # 日次集計
    path('daily/list/', DailySummaryListView.as_view()),
    path('daily/export/', DailySummaryExportView.as_view()),
    path('daily/<int:pk>/detail/', DailySummaryDetailView.as_view()),
    
    # 月次集計
    path('monthly/list/', MonthlySummaryListView.as_view()),
    path('monthly/export/', MonthlySummaryExportView.as_view()),
    path('monthly/<int:pk>/detail/', MonthlySummaryDetailView.as_view()),

    # グラフ用追加
    path('daily/chart/', DailySummaryChartView.as_view()),
    path('monthly/chart/', MonthlySummaryChartView.as_view()),
]