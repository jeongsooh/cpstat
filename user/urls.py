from django.urls import path
from . import views

urlpatterns = [
  path('', views.UserList.as_view()),
  path('register/', views.UserCreateView.as_view()),
  path('<int:pk>/', views.UserDetail.as_view()),
  path('<int:pk>/update', views.UserUpdateView.as_view()),
  path('<int:pk>/delete/', views.UserDeleteView.as_view()),
]