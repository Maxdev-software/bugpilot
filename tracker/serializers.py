from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Comment, IngestLog, Project, Ticket


class ProjectSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'name', 'slug', 'description', 'created_by', 'member_count', 'created_at']
        read_only_fields = ['created_by', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count()

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class IngestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = IngestLog
        fields = [
            'id', 'project', 'app_name', 'environment', 'level',
            'message', 'stacktrace', 'metadata', 'received_at',
            'processing_status', 'celery_task_id',
        ]
        read_only_fields = ['received_at', 'processing_status', 'celery_task_id']


class IngestInputSerializer(serializers.Serializer):
    """Used by the public ingest endpoint."""
    app_name = serializers.CharField(max_length=120)
    environment = serializers.CharField(max_length=60, default='production')
    level = serializers.ChoiceField(choices=IngestLog.Level.choices, default='ERROR')
    message = serializers.CharField()
    stacktrace = serializers.CharField(allow_blank=True, default='')
    metadata = serializers.DictField(child=serializers.JSONField(), default=dict)
    project_slug = serializers.SlugField(required=False, allow_blank=True)


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'body', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    assignee = UserSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    display_id = serializers.CharField(read_only=True)
    comment_count = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = [
            'id', 'display_id', 'title', 'priority', 'status',
            'assignee', 'reporter', 'created_at', 'updated_at',
            'ai_summary', 'comment_count', 'project',
        ]

    def get_comment_count(self, obj):
        return obj.comments.count()


class TicketDetailSerializer(serializers.ModelSerializer):
    assignee = UserSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    assignee_id = serializers.PrimaryKeyRelatedField(
        source='assignee',
        queryset=__import__('accounts').models.User.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    display_id = serializers.CharField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    ingest_log = IngestLogSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'display_id', 'project', 'ingest_log',
            'title', 'description', 'priority', 'status',
            'ai_summary', 'ai_root_cause', 'ai_fix_suggestion',
            'ai_analysed_at', 'ai_model_used',
            'assignee', 'assignee_id', 'reporter',
            'created_at', 'updated_at', 'resolved_at',
            'comments',
        ]
        read_only_fields = [
            'reporter', 'created_at', 'updated_at', 'resolved_at',
            'ai_analysed_at', 'ai_model_used',
        ]


class TicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = ['project', 'title', 'description', 'priority', 'status', 'assignee']

    def create(self, validated_data):
        validated_data['reporter'] = self.context['request'].user
        return super().create(validated_data)


class StatsSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    open = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    resolved = serializers.IntegerField()
    critical = serializers.IntegerField()
    bug = serializers.IntegerField()
    warning = serializers.IntegerField()
    ai_analysed = serializers.IntegerField()
