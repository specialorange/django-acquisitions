"""
Celery tasks for customer acquisition.

Tasks are optional - if Celery is not installed or ACQUISITIONS_USE_CELERY=False,
the underlying functions can be called directly.
"""

# Import tasks only if Celery is available
try:
    from .outreach_tasks import process_scheduled_outreach_task, send_campaign_step_task
    from .reminder_tasks import send_follow_up_reminders_task

    __all__ = [
        "process_scheduled_outreach_task",
        "send_campaign_step_task",
        "send_follow_up_reminders_task",
    ]
except ImportError:
    # Celery not installed
    __all__ = []
