from django.contrib import admin
from django.utils.html import format_html
from .models import Comment, IngestLog, Project, Ticket


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_by', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['members']


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['display_id', 'title', 'priority_badge', 'status', 'assignee', 'ai_done', 'created_at']
    list_filter = ['priority', 'status', 'project']
    search_fields = ['title', 'description', 'ai_summary']
    readonly_fields = ['display_id', 'serial', 'ai_analysed_at', 'ai_model_used', 'created_at', 'updated_at']
    inlines = [CommentInline]
    fieldsets = (
        (None, {'fields': ('display_id', 'project', 'title', 'description', 'priority', 'status', 'assignee', 'reporter')}),
        ('AI Analysis', {'fields': ('ai_summary', 'ai_root_cause', 'ai_fix_suggestion', 'ai_analysed_at', 'ai_model_used')}),
        ('Meta', {'fields': ('created_at', 'updated_at', 'resolved_at')}),
    )

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        colors = {'critical': '#E24B4A', 'bug': '#EF9F27', 'warning': '#378ADD', 'info': '#639922'}
        color = colors.get(obj.priority, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:11px">{}</span>',
            color, obj.get_priority_display()
        )

    @admin.display(boolean=True, description='AI done')
    def ai_done(self, obj):
        return bool(obj.ai_analysed_at)


@admin.register(IngestLog)
class IngestLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'app_name', 'level', 'environment', 'processing_status', 'received_at']
    list_filter = ['level', 'processing_status', 'environment']
    search_fields = ['app_name', 'message']
    readonly_fields = ['id', 'received_at', 'celery_task_id']
