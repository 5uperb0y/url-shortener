from django.shortcuts import render, get_object_or_404, redirect
from django.db import IntegrityError
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import UrlMaps, Clicks
import secrets

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


def redirect_url(request, slug: str):
    """
    Redirect slugs to their original urls
    """
    url_map = get_object_or_404(UrlMaps, slug=slug)
    # TODO: It takes time to record IP addresses during redirection,
    # especially when many people click hot URLs (e.g., google.com).
    ip = get_client_ip(request)
    Clicks.objects.create(slug=url_map, ip=ip)
    return redirect(url_map.url)


# avoid unauthorized POST
@login_required
def shorten_url(request):
    """
    Generate 7-character slugs for urls
    """
    if request.method == 'POST':
        url = request.POST.get('url')
        # Handle slug collisions
        retry = 0
        while retry < 5:
            try:
                slug = generate_slug(7)
                UrlMaps.objects.create(user=request.user, url=url, slug=slug)
                # Redirect to main page, avoiding duplicate submission
                return redirect('shorten_url')
            except IntegrityError:
                retry += 1
        messages.error(request, "縮網址失敗，請稍候再試。")
        return redirect('shorten_url')
    url_maps = UrlMaps.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'index.html', {'url_maps': url_maps})


@login_required
def summarize_clicks(request, slug: str):
    # Return 404 when the slug does not exist or does not belong to the current user,
    # similar to GitHub returning 404 when accessing a private repository.
    url_map = get_object_or_404(UrlMaps, user=request.user, slug=slug)
    clicks = Clicks.objects.filter(slug=url_map).order_by('-created_at')
    return render(request, 'clicks.html', {'clicks': clicks, 'url_map': url_map})