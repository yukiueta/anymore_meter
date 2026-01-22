from django.urls import path
from .views import (
    MeterListView,
    MeterCreateView,
    MeterDetailView,
    MeterUpdateView,
    MeterDeleteView,
    MeterBRouteUpdateView,
    MeterAssignView,
    MeterUnassignView,
    MeterAssignmentUpdateView,
    MeterAssignmentDeleteView,
    MeterSyncProjectView,
    MeterBulkCreateView,
    MeterExportView,
    SekouCustomerSearchView
)
from .receive_api import MeterReceiveView
from .b_route_api import MeterBRouteCommandView

urlpatterns = [
    path('list/', MeterListView.as_view()),
    path('create/', MeterCreateView.as_view()),
    path('bulk/create/', MeterBulkCreateView.as_view()),
    path('export/', MeterExportView.as_view()),
    path('<int:pk>/detail/', MeterDetailView.as_view()),
    path('<int:pk>/update/', MeterUpdateView.as_view()),
    path('<int:pk>/delete/', MeterDeleteView.as_view()),
    path('<int:pk>/b-route/', MeterBRouteUpdateView.as_view()),
    path('<int:pk>/assign/project/', MeterAssignView.as_view()),
    path('<int:pk>/unassign/project/', MeterUnassignView.as_view()),
    path('<int:pk>/assignment/<int:assignment_id>/update/', MeterAssignmentUpdateView.as_view()),
    path('<int:pk>/assignment/<int:assignment_id>/delete/', MeterAssignmentDeleteView.as_view()),
    path('<int:pk>/sync/project/', MeterSyncProjectView.as_view(), name='meter-sync-project'),
    path('sekou/customers/', SekouCustomerSearchView.as_view()),

    path('receive/', MeterReceiveView.as_view()),  # Lambda受信
    path('<int:pk>/b-route/send/', MeterBRouteCommandView.as_view()),
]