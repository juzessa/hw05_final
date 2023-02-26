from django.core.paginator import Paginator

from .constants import FIRST_TEN


def paginator(request, posts):
    paginator = Paginator(posts, FIRST_TEN)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
