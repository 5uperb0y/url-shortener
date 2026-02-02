import secrets

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from .forms import UrlForm
from .models import Link
from .tasks import record_click


def get_client_ip(request):
    """Get the client's IP address, accounting for proxies."""
    # Source - https://stackoverflow.com/a
    # Posted by yanchenko, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-01-24, License - CC BY-SA 4.0
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def create_new_link(current_user, original_url):
    """Create a link and assign an unique random slug."""
    available_chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    slug_length = 7  # Longer length reduces collisions with random generation (62^7 = ~3.5 trillion)
    max_attempts = 5  # Sufficient for ~4 attempts when 75% of slug space is occupied

    attempts = 0
    while attempts < max_attempts:
        new_slug = ''.join(secrets.choice(available_chars) for _ in range(slug_length))
        try:
            new_link = Link.objects.create(
                user=current_user, url=original_url, slug=new_slug
            )
            return new_link
        except IntegrityError:  # Slug collision occurred, retry
            attempts += 1
    return None


@ratelimit(key='ip', rate='7/s', method='GET')  # avg CPS ~ 7, above these likely bots
@ratelimit(key='ip', rate='60/m', method='GET')
def redirect_url(request, query_slug: str):
    """Redirect slugs to their original URLs and record click events."""
    target_link = get_object_or_404(Link, slug=query_slug)
    user_ip = get_client_ip(request)
    record_click.delay(
        target_link_id=target_link.id, user_ip=user_ip, clicked_at=timezone.now()
    )
    return redirect(target_link.url)


@login_required
@ratelimit(key='user', rate='2/s', method='POST')  # Prevents accidental double-clicks
@ratelimit(key='user', rate='20/m', method='POST')  # ~3s per link (manual testing)
def shorten_url(request):
    """Shorten URLs and display user's links."""
    if request.method == 'POST':
        form = UrlForm(request.POST, request=request)
        if form.is_valid():
            original_url = form.cleaned_data['url']
            new_link = create_new_link(
                current_user=request.user, original_url=original_url
            )
            if new_link:
                return redirect('shorten_url')
            else:
                form.add_error(None, '縮網址失敗，請稍候再試。')
    else:
        form = UrlForm(request=request)

    links = request.user.links.all()
    p = Paginator(links, 10)
    page_obj = p.get_page(request.GET.get('page'))
    return render(request, 'index.html', {'form': form, 'page_obj': page_obj})


@login_required
@ratelimit(key='user', rate='2/s', method='GET')  # Consider page refreshes
@ratelimit(key='user', rate='20/m', method='GET')
def summarize_clicks(request, query_slug: str):
    """Show click counts for a link."""
    # Return 404 when the slug does not exist or does not belong to the current user,
    # similar to GitHub returning 404 when accessing a private repository.
    target_link = get_object_or_404(Link, user=request.user, slug=query_slug)
    clicks = target_link.clicks.all()
    p = Paginator(clicks, 30)
    page_obj = p.get_page(request.GET.get('page'))
    return render(request, 'clicks.html', {'link': target_link, 'page_obj': page_obj})
