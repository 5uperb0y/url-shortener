from datetime import datetime

from celery import shared_task
from django.db import IntegrityError

from .models import Click


@shared_task(ignore_result=True)
def record_click(target_link_id: int, user_ip: str, clicked_at: datetime):
    """Record a click event for a link."""

    try:
        Click.objects.create(link_id=target_link_id, ip=user_ip, clicked_at=clicked_at)
    except IntegrityError:
        # TODO: use logger instead.
        print('Link ID not found.')
