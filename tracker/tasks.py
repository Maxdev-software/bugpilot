import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger('tracker')


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    name='tracker.tasks.analyse_ingest_log',
)
def analyse_ingest_log(self, ingest_log_id: str):
    from .models import IngestLog, Ticket
    from .services import analyse_error

    try:
        log = IngestLog.objects.select_related('project').get(pk=ingest_log_id)
    except IngestLog.DoesNotExist:
        logger.error('IngestLog %s not found', ingest_log_id)
        return

    log.processing_status = IngestLog.ProcessingStatus.PROCESSING
    log.save(update_fields=['processing_status'])

    try:
        analysis = analyse_error(
            app_name=log.app_name,
            environment=log.environment,
            level=log.level,
            message=log.message,
            stacktrace=log.stacktrace,
        )
    except Exception as exc:
        logger.warning('AI analysis failed for %s: %s. Retrying...', ingest_log_id, exc)
        log.processing_status = IngestLog.ProcessingStatus.FAILED
        log.save(update_fields=['processing_status'])
        raise self.retry(exc=exc)

    title_raw = log.message.strip().splitlines()[0]
    title = title_raw[:295] if title_raw else f'{log.app_name} {log.level} error'

    from django.conf import settings
    ticket = Ticket(
        ingest_log=log,
        project=log.project,
        title=title,
        description=f'Auto-created from ingest log {log.id}\n\nStacktrace:\n{log.stacktrace}',
        priority=analysis['priority'],
        status=Ticket.Status.OPEN,
        ai_summary=analysis.get('summary', ''),
        ai_root_cause=analysis.get('root_cause', ''),
        ai_fix_suggestion=analysis.get('fix_suggestion', ''),
        ai_analysed_at=timezone.now(),
        ai_model_used=settings.OPENROUTER_MODEL,
    )
    ticket.save()

    log.processing_status = IngestLog.ProcessingStatus.DONE
    log.save(update_fields=['processing_status'])

    logger.info(
        'Ticket %s created from ingest log %s (priority=%s)',
        ticket.display_id,
        ingest_log_id,
        ticket.priority,
    )
    return {'ticket_id': str(ticket.id), 'display_id': ticket.display_id}


@shared_task(name='tracker.tasks.reanalyse_ticket')
def reanalyse_ticket(ticket_id: str):
    """Re-run AI analysis on an existing ticket (e.g. triggered by Teamlead)."""
    from .models import Ticket
    from .services import analyse_error

    try:
        ticket = Ticket.objects.select_related('ingest_log').get(pk=ticket_id)
    except Ticket.DoesNotExist:
        logger.error('Ticket %s not found for reanalysis', ticket_id)
        return

    log = ticket.ingest_log
    if not log:
        logger.warning('Ticket %s has no ingest log, cannot reanalyse', ticket_id)
        return

    try:
        analysis = analyse_error(
            app_name=log.app_name,
            environment=log.environment,
            level=log.level,
            message=log.message,
            stacktrace=log.stacktrace,
        )
    except Exception as exc:
        logger.error('Reanalysis failed for ticket %s: %s', ticket_id, exc)
        return

    from django.conf import settings
    ticket.ai_summary = analysis.get('summary', '')
    ticket.ai_root_cause = analysis.get('root_cause', '')
    ticket.ai_fix_suggestion = analysis.get('fix_suggestion', '')
    ticket.ai_analysed_at = timezone.now()
    ticket.ai_model_used = settings.OPENROUTER_MODEL
    ticket.priority = analysis.get('priority', ticket.priority)
    ticket.save(update_fields=[
        'ai_summary', 'ai_root_cause', 'ai_fix_suggestion',
        'ai_analysed_at', 'ai_model_used', 'priority',
    ])
    logger.info('Ticket %s reanalysed, new priority=%s', ticket.display_id, ticket.priority)
    return {'ticket_id': str(ticket.id), 'priority': ticket.priority}
