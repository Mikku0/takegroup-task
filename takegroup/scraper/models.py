from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=500)
    original_content = models.TextField()
    plain_text = models.TextField()
    source_url = models.URLField(unique=True, max_length=1000)
    publication_date = models.CharField(max_length=19)  # dd.mm.yyyy HH:mm:ss
    scraped_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scraped_at']

    def __str__(self):
        return self.title