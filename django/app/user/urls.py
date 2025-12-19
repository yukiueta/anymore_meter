from django.urls import path
from .views import (
    UserListView,
    UserCreateView,
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    UserMeView,
)

urlpatterns = [
    path('list/', UserListView.as_view()),
    path('create/', UserCreateView.as_view()),
    path('<int:pk>/detail/', UserDetailView.as_view()),
    path('<int:pk>/update/', UserUpdateView.as_view()),
    path('<int:pk>/delete/', UserDeleteView.as_view()),
    path('me/', UserMeView.as_view()),
]