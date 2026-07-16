from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('projects', views.ProjectViewSet, basename='project')
router.register('tickets', views.TicketViewSet, basename='ticket')

urlpatterns = [
    path('', include(router.urls)),

    # Ingest
    path('ingest/log/', views.ingest_log, name='ingest-log'),
    path('ingest/logs/', views.IngestLogListView.as_view(), name='ingest-log-list'),

    # Comments
    path(
        'tickets/<uuid:ticket_pk>/comments/',
        views.CommentListCreateView.as_view(),
        name='ticket-comments',
    ),
    path(
        'tickets/<uuid:ticket_pk>/comments/<int:pk>/',
        views.CommentDetailView.as_view(),
        name='ticket-comment-detail',
    ),

    path('stats/', views.stats, name='stats'),
]
