from django.db import models

# Create your models here.
class UrlMaps(models.Model):
    """
    Map urls and their slugs
    """
    url = models.URLField(help_text='An url to be shorten')
    slug = models.CharField(max_length=7, unique=True, help_text='A random 7-character code (i.e. [a-zA-Z0-9])')
    created_at = models.DateTimeField(auto_now_add=True)

class Clicks(models.Model):
    """
    Visitors' ip for each slug
    """
    slug = models.ForeignKey(UrlMaps, on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)