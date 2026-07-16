from rest_framework.permissions import BasePermission, SAFE_METHODS


class TicketPermission(BasePermission):
    """
    - Admin/Teamlead: full CRUD
    - Developer: read + update own assigned tickets (status/comments)
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_teamlead:
            return True
        if request.method in SAFE_METHODS:
            return True
        # Developer can update tickets assigned to them
        if user.role == 'developer' and obj.assignee == user:
            return True
        return False


class IngestPermission(BasePermission):
    """
    The ingest endpoint accepts a static shared token (no user account needed).
    Used by external applications posting their crash logs.
    """

    def has_permission(self, request, view):
        from django.conf import settings
        token = request.headers.get('X-Ingest-Token', '')
        return token == settings.INGEST_API_TOKEN
