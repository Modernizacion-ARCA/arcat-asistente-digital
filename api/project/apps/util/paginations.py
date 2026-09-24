from rest_framework_json_api.pagination import JsonApiPageNumberPagination


class LargePagination(JsonApiPageNumberPagination):
    max_page_size = 300
    page_size_query_param = 'page_size'
