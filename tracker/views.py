import logging

from django.db.models import Count, Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.permissions import IsAdminRole, IsTeamLeadOrAdmin
from .models import Comment, IngestLog, Project, Ticket
from .permissions import IngestPermission, TicketPermission
from .serializers import (
    CommentSerializer,
    IngestInputSerializer,
    IngestLogSerializer,
    ProjectSerializer,
    StatsSerializer,
    TicketCreateSerializer,
    TicketDetailSerializer,
    TicketListSerializer,
)
from .tasks import analyse_ingest_log, reanalyse_ticket

logger = logging.getLogger('tracker')



@api_view(['POST'])
@permission_classes([IngestPermission])
def ingest_log(request):
    serializer = IngestInputSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    project = None
    if data.get('project_slug'):
        project = Project.objects.filter(slug=data['project_slug']).first()

    log = IngestLog.objects.create(
        project=project,
        app_name=data['app_name'],
        environment=data['environment'],
        level=data['level'],
        message=data['message'],
        stacktrace=data.get('stacktrace', ''),
        metadata=data.get('metadata', {}),
    )

    task = analyse_ingest_log.delay(str(log.id))
    log.celery_task_id = task.id
    log.save(update_fields=['celery_task_id'])

    logger.info('Ingest log %s received from %s, task=%s', log.id, data['app_name'], task.id)

    return Response(
        {
            'log_id': str(log.id),
            'task_id': task.id,
            'status': 'queued',
            'message': 'Log received. AI analysis running in background.',
        },
        status=status.HTTP_202_ACCEPTED,
    )



class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return Project.objects.annotate(ticket_count=Count('tickets')).all()
        return user.projects.annotate(ticket_count=Count('tickets')).all()

    def get_permissions(self):
        if self.action in ('create', 'destroy'):
            return [IsTeamLeadOrAdmin()]
        return super().get_permissions()

    @action(detail=True, methods=['post', 'delete'], url_path='members/(?P<user_id>[^/.]+)')
    def manage_member(self, request, pk=None, user_id=None):
        project = self.get_object()
        from accounts.models import User
        user = generics.get_object_or_404(User, pk=user_id)
        if request.method == 'POST':
            project.members.add(user)
            return Response({'detail': f'{user.username} added.'})
        project.members.remove(user)
        return Response(status=status.HTTP_204_NO_CONTENT)



class TicketViewSet(viewsets.ModelViewSet):
    permission_classes = [TicketPermission]

    def get_queryset(self):
        qs = Ticket.objects.select_related(
            'assignee', 'reporter', 'project', 'ingest_log'
        ).prefetch_related('comments__author')

        params = self.request.query_params
        if priority := params.get('priority'):
            qs = qs.filter(priority=priority)
        if status_val := params.get('status'):
            qs = qs.filter(status=status_val)
        if project_id := params.get('project'):
            qs = qs.filter(project_id=project_id)
        if assignee_id := params.get('assignee'):
            qs = qs.filter(assignee_id=assignee_id)
        if search := params.get('search'):
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))

        return qs

    def get_serializer_class(self):
        if self.action == 'list':
            return TicketListSerializer
        if self.action == 'create':
            return TicketCreateSerializer
        return TicketDetailSerializer

    @action(detail=True, methods=['post'], url_path='reanalyse', permission_classes=[IsTeamLeadOrAdmin])
    def reanalyse(self, request, pk=None):
        ticket = self.get_object()
        task = reanalyse_ticket.delay(str(ticket.id))
        return Response({'task_id': task.id, 'detail': 'Reanalysis queued.'})

    @action(detail=True, methods=['patch'], url_path='assign')
    def assign(self, request, pk=None):
        ticket = self.get_object()
        from accounts.models import User
        user_id = request.data.get('assignee_id')
        if user_id:
            assignee = generics.get_object_or_404(User, pk=user_id)
            ticket.assignee = assignee
        else:
            ticket.assignee = None
        ticket.save(update_fields=['assignee', 'updated_at'])
        return Response(TicketDetailSerializer(ticket).data)

    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        ticket = self.get_object()
        new_status = request.data.get('status')
        if new_status not in dict(Ticket.Status.choices):
            return Response({'detail': 'Invalid status.'}, status=status.HTTP_400_BAD_REQUEST)
        ticket.status = new_status
        ticket.save(update_fields=['status', 'updated_at', 'resolved_at'])
        return Response({'id': str(ticket.id), 'status': ticket.status})



class CommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(
            ticket_id=self.kwargs['ticket_pk']
        ).select_related('author')

    def perform_create(self, serializer):
        ticket = generics.get_object_or_404(Ticket, pk=self.kwargs['ticket_pk'])
        serializer.save(ticket=ticket, author=self.request.user)


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(ticket_id=self.kwargs['ticket_pk'])

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user.is_teamlead



class IngestLogListView(generics.ListAPIView):
    serializer_class = IngestLogSerializer
    permission_classes = [IsTeamLeadOrAdmin]

    def get_queryset(self):
        qs = IngestLog.objects.all()
        if status_val := self.request.query_params.get('status'):
            qs = qs.filter(processing_status=status_val)
        return qs



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def stats(request):
    qs = Ticket.objects.all()
    if not request.user.is_teamlead:
        qs = qs.filter(
            Q(assignee=request.user) | Q(reporter=request.user)
        )
    data = {
        'total': qs.count(),
        'open': qs.filter(status='open').count(),
        'in_progress': qs.filter(status='in_progress').count(),
        'resolved': qs.filter(status='resolved').count(),
        'critical': qs.filter(priority='critical').count(),
        'bug': qs.filter(priority='bug').count(),
        'warning': qs.filter(priority='warning').count(),
        'ai_analysed': qs.exclude(ai_analysed_at=None).count(),
    }
    return Response(StatsSerializer(data).data)
