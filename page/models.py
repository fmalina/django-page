import time
from datetime import datetime
from email.utils import formatdate

from django.db import models
from django.template.defaultfilters import slugify

from . import app_settings
from .utils import meta_desc


class Page(models.Model):
    """Editable pages: help centre, blog, press section etc."""
    parent = models.ForeignKey(
        'self', verbose_name="Section", blank=True, null=True,
        limit_choices_to={'id__in': app_settings.PAGE_PARENT_IDS},
        on_delete=models.SET_NULL
    )
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.CharField(max_length=150, null=True, blank=True)
    slug = models.SlugField(
        max_length=75, db_index=True,
        verbose_name='URL slug'
    )
    active = models.BooleanField(default=False)
    updated_at = models.DateTimeField(default=datetime.now, editable=False)
    created_at = models.DateTimeField(default=datetime.now, editable=False)
    
    def rfc2822_date(self):
        return formatdate(time.mktime(self.created_at.timetuple()))
    
    def get_absolute_url(self):
        if self.parent:
            return f'/{self.parent.slug}/{self.slug}'
        else:
            return f'/{self.slug}'
    
    def teaser(self):
        return self.body.split('<hr')[0]
    
    def desc(self):
        return meta_desc(self.body, self.title)

    def children(self):
        return Page.objects.filter(parent=self).all()
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        if not self.slug:
            self.slug = slugify(self.title)
        super(Page, self).save(*args, **kwargs)
    
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['parent__slug', 'slug']


class Redirect(models.Model):
    """Permanent redirects from legacy URLs to their new counterparts"""
    old_path = models.CharField(
        'redirect from', max_length=200, db_index=True, unique=True,
        help_text=' - absolute path, excluding the domain name. Example: "/some/path"'
    )
    new_path = models.CharField(
        'redirect to', max_length=200, blank=True,
        help_text=' - either an absolute path (as above) or a full URL starting with "http(s)://"'
    )
    usage_count = models.PositiveIntegerField(default=0, blank=True, null=True, editable=False)
    last_used = models.DateTimeField(default=datetime.now, editable=False)

    def get_absolute_url(self):
        return self.old_path

    def __str__(self):
        return f'{self.old_path} → {self.new_path}'

    class Meta:
        ordering = ['old_path']
