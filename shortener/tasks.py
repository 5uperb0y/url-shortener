from celery import shared_task

from .models import Click


@shared_task(ignore_result=True)
def record_click(target_link_id: int, user_ip: str, clicked_at: str):
    Click.objects.create(link_id=target_link_id, ip=user_ip, clicked_at=clicked_at)
