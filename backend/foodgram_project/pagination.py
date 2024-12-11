from rest_framework.pagination import PageNumberPagination


class Pagination(PageNumberPagination):
    """
    Pagination for Recipe- and CustomUserViewSet.
    """

    page_size = 100
    page_size_query_param = 'limit'
    max_page_size = 1000
