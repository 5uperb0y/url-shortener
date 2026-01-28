import secrets

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import render, get_object_or_404, redirect

from .models import Link, Click 
from .forms import UrlForm

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


def redirect_url(request, query_slug: str):
    """
    Redirect slugs to their original urls
    """
    target_link = get_object_or_404(Link, slug=query_slug)
    # TODO: It takes time to record IP addresses during redirection,
    # especially when many people click hot URLs (e.g., google.com).
    user_ip = get_client_ip(request)
    Click.objects.create(link=target_link, ip=user_ip)
    return redirect(target_link.url)


# avoid unauthorized POST
@login_required
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
    links = Link.objects.filter(user=request.user)
    return render(request, 'index.html', {'form': form, 'links': links})


@login_required
def summarize_clicks(request, query_slug: str):
    # Return 404 when the slug does not exist or does not belong to the current user,
    # similar to GitHub returning 404 when accessing a private repository.
    target_link = get_object_or_404(Link, user=request.user, slug=query_slug)
    clicks = Click.objects.filter(link=target_link)
    return render(request, 'clicks.html', {'clicks': clicks, 'link': target_link})