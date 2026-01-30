from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Link(models.Model):
    """
    Map urls and their slugs
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='links')
    url = models.URLField(max_length=2048, help_text='An url to be shorten')
    slug = models.CharField(max_length=7, unique=True, help_text='A random 7-character code (i.e. [a-zA-Z0-9])')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Click(models.Model):
    """
    Visitors' ip for each slug
    """
    link = models.ForeignKey(Link, on_delete=models.CASCADE, related_name='clicks')
    ip = models.GenericIPAddressField()
    clicked_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-clicked_at']