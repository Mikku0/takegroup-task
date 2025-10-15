from rest_framework import serializers
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = ['id', 'title', 'original_content', 'plain_text', 
                  'source_url', 'publication_date', 'scraped_at']