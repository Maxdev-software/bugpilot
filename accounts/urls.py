from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout),
    path('me/', views.me),
    path('users/', views.UserListView.as_view()),
    path('users/<int:pk>/role/', views.change_role),
]
