from django.shortcuts import render, get_object_or_404, redirect
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


def shorten_url(request):
    """
    Generate 7-character slugs for urls
    """
    if request.method == 'POST':
        url = request.POST.get('url')
        # TODO: Handle slug collisions
        slug = generate_slug(7)
        UrlMaps.objects.create(url=url, slug=slug)
        # Redirect to mainpage, avoiding duplicate submission
        return redirect('shorten_url')
    url_maps = UrlMaps.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'url_maps': url_maps})


def summarize_clicks(request, slug: str):
    url_map = get_object_or_404(UrlMaps, slug=slug)
    clicks = Clicks.objects.filter(slug=url_map).order_by('-created_at')
    return render(request, 'clicks.html', {'clicks': clicks, 'url_map': url_map})