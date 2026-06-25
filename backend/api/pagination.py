"""Пагинация API проекта Foodgram."""

from rest_framework.pagination import PageNumberPagination


class FoodgramPagination(PageNumberPagination):
    """Постраничная пагинация с параметром limit."""

    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100
