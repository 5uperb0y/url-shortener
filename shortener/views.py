import secrets

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .forms import UrlForm
from .models import Click, Link
from .tasks import record_click


# Create your views here.
def get_client_ip(request):
    # Source - https://stackoverflow.com/a
    # Posted by yanchenko, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-01-24, License - CC BY-SA 4.0
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def generate_slug(length: int = 7):
    chars='0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    return ''.join(secrets.choice(chars) for _ in range(length))



@ratelimit(key='ip', rate='7/s', method='GET') # avg CPS ~ 6.69, above these likely bots
@ratelimit(key='ip', rate='60/m', method='GET')
def redirect_url(request, query_slug: str):
    """
    Redirect slugs to their original urls
    """
    target_link = get_object_or_404(Link, slug=query_slug)
    user_ip = get_client_ip(request)
    record_click.delay(
        target_link_id=target_link.id,
        user_ip=user_ip,
        clicked_at=timezone.now()
    )
    return redirect(target_link.url)


# avoid unauthorized POST
@login_required
@ratelimit(key='user', rate='2/s', method='POST')   # revents accidental double-clicks
@ratelimit(key='user', rate='20/m', method='POST')  # Manual testing shows ~3s per link creation
def shorten_url(request):
    """
    Generate 7-character slugs for urls
    """
    if request.method == 'POST':
        form = UrlForm(request.POST, request=request)
        if form.is_valid():
            original_url = form.cleaned_data['url']
            # Handle slug collisions
            # When 75% of slug space is occupied, a 7-character slug typically requires
            # ~4 attempts to find a unique one. If more attempts are needed, this may
            # indicate issues beyond normal collisions
            # See details at https://medium.com/@sandeep4.verma/system-design-scalable-url-shortener-service-like-tinyurl-106f30f23a82
            attempts = 0
            while attempts < 5:
                try:
                    Link.objects.create(user=request.user, url=original_url, slug=generate_slug(7))
                    # Redirect to main page, avoiding duplicate submission
                    return redirect('shorten_url')
                except IntegrityError:
                    attempts += 1
            form.add_error(None, "縮網址失敗，請稍候再試。")
    else:
        form = UrlForm(request=request)

    links = request.user.links.all()
    p = Paginator(links, 10)
    page_obj = p.get_page(request.GET.get('page'))
    return render(request, 'index.html', {'form': form, 'page_obj': page_obj})


@login_required
@ratelimit(key='user', rate='2/s', method='GET')  # include refresh
@ratelimit(key='user', rate='20/m', method='GET')
def summarize_clicks(request, query_slug: str):
    # Return 404 when the slug does not exist or does not belong to the current user,
    # similar to GitHub returning 404 when accessing a private repository.
    target_link = get_object_or_404(Link, user=request.user, slug=query_slug)
    clicks = target_link.clicks.all()
    p = Paginator(clicks, 30)
    page_obj = p.get_page(request.GET.get('page'))
    return render(request, 'clicks.html', {'link': target_link, 'page_obj': page_obj})