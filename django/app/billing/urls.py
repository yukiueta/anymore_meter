from django.urls import path
from . import views

urlpatterns = [
    # BillingCalendar
    path('calendar/', views.BillingCalendarListView.as_view()),
    path('calendar/import/', views.BillingCalendarImportView.as_view()),
    path('calendar/delete/', views.BillingCalendarDeleteView.as_view()),
    path('calendar/export/', views.BillingCalendarExportView.as_view()),
    path('calendar/summary/', views.BillingCalendarSummaryView.as_view()),
    path('zones/', views.ZoneChoicesView.as_view()),

    # BillingSummary
    path('summary/', views.BillingSummaryGroupListView.as_view()),
    path('summary/detail/', views.BillingSummaryDetailListView.as_view()),
    path('summary/export/', views.BillingSummaryExportView.as_view()),
    path('summary/meter/', views.BillingSummaryMeterView.as_view()),
    path('summary/by-project/', views.BillingSummaryByProjectView.as_view()),
    path('summary/chart/', views.BillingSummaryChartView.as_view()),

    # Anymore連携用
    path('summary/pending/', views.BillingSummaryPendingView.as_view()),
    path('summary/mark-processed/', views.BillingSummaryMarkProcessedView.as_view()),
    path('summary/errors/', views.BillingSummaryErrorsView.as_view()),  
    path('summary/retry/', views.BillingSummaryRetryView.as_view()),
    path('summary/pending/by-month/', views.BillingSummaryPendingByMonthView.as_view()),
    path('summary/matrix/', views.BillingSummaryMatrixView.as_view()),
    path('summary/all/by-month/', views.BillingSummaryAllByMonthView.as_view()),
]