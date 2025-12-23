from django.urls import path
from . import views

urlpatterns = [
    path('readings/', views.MypageReadingsView.as_view(), name='mypage-readings'),
]