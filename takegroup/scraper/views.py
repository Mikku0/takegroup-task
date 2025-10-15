from rest_framework import viewsets
from rest_framework.response import Response
from .models import Article
from .serializers import ArticleSerializer
from urllib.parse import urlparse

class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        
        source = request.query_params.get('source', None)
        if source:
            queryset = queryset.filter(source_url__icontains=source)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)