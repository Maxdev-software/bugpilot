import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Project(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class IngestLog(models.Model):
    """Raw log entry received from external application via POST /api/v1/ingest/log/"""

    class Level(models.TextChoices):
        DEBUG = 'DEBUG', 'Debug'
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CRITICAL = 'CRITICAL', 'Critical'

    class ProcessingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='ingest_logs',
        null=True,
        blank=True,
    )
    app_name = models.CharField(max_length=120)
    environment = models.CharField(max_length=60, default='production')
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.ERROR)
    message = models.TextField()
    stacktrace = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    received_at = models.DateTimeField(default=timezone.now)
    processing_status = models.CharField(
        max_length=20,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
    )
    celery_task_id = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-received_at']
        db_table = 'tracker_ingest_log'

    def __str__(self):
        return f'[{self.level}] {self.app_name}: {self.message[:60]}'


class Ticket(models.Model):
    class Priority(models.TextChoices):
        CRITICAL = 'critical', 'Critical'
        BUG = 'bug', 'Bug'
        WARNING = 'warning', 'Warning'
        INFO = 'info', 'Info'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
        WONT_FIX = 'wont_fix', "Won't Fix"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    serial = models.PositiveIntegerField(editable=False)  # BUG-001 display id
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tickets',
        null=True,
        blank=True,
    )
    ingest_log = models.OneToOneField(
        IngestLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket',
    )
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.BUG)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    # AI analysis
    ai_summary = models.TextField(blank=True)
    ai_root_cause = models.TextField(blank=True)
    ai_fix_suggestion = models.TextField(blank=True)
    ai_analysed_at = models.DateTimeField(null=True, blank=True)
    ai_model_used = models.CharField(max_length=120, blank=True)

    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_tickets',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        db_table = 'tracker_ticket'

    def save(self, *args, **kwargs):
        if not self.serial:
            last = Ticket.objects.order_by('-serial').first()
            self.serial = (last.serial + 1) if last else 1
        if self.status == self.Status.RESOLVED and not self.resolved_at:
            self.resolved_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'BUG-{self.serial:03d}: {self.title[:60]}'

    @property
    def display_id(self):
        return f'BUG-{self.serial:03d}'


class Comment(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments',
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on {self.ticket.display_id}'
