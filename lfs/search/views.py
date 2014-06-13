# python imports
import json

# django imports
from django.db.models import Q
from django.core.exceptions import FieldError
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string

# lfs imports
from lfs.catalog.models import Category
from lfs.catalog.models import Product
from lfs.catalog.settings import STANDARD_PRODUCT, PRODUCT_WITH_VARIANTS, VARIANT
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def livesearch(request, template_name="lfs/search/livesearch_results.html"):
    """
    """
    q = request.GET.get("q", "")

    if q == "":
        result = json.dumps({
            "state": "failure",
        })
    else:
        # Products
        query = Q(active=True) & \
                ( Q(name__icontains=q) | \
                  Q(manufacturer__name__icontains=q) | \
                  Q(sku_manufacturer__icontains=q) ) & \
                Q(sub_type__in=(STANDARD_PRODUCT, PRODUCT_WITH_VARIANTS, VARIANT))

        temp = Product.objects.filter(query)
        total = temp.count()
        products = temp[0:5]

        products = render_to_string(template_name, RequestContext(request, {
            "products": products,
            "q": q,
            "total": total,
        }))

        result = json.dumps({
            "state": "success",
            "products": products,
        })
    return HttpResponse(result, mimetype='application/json')

def search(request, template_name="lfs/search/search_results.html"):
    """Returns the search result according to given query (via get request)
    ordered by the globally set sorting.
    """
    q = request.GET.get("q", "")

    if q == "":
        products = []
    else:
        query = Q(active=True) & \
                ( Q(name__icontains=q) | \
                  Q(manufacturer__name__icontains=q) | \
                  Q(sku_manufacturer__icontains=q) ) & \
                Q(sub_type__in=(STANDARD_PRODUCT, PRODUCT_WITH_VARIANTS, VARIANT))

        products = Product.objects.filter(query)

        # Sorting
        sorting = request.session.get("sorting")
        if sorting:
            products = products.order_by(sorting)

    total = products.count()

    limit = int(request.session.get("items_per_page", "10"))
    paginator = Paginator(products, limit)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    adj = 2
    pages = [n for n in range(products.number - adj, products.number + adj + 1) if 0 < n <= paginator.num_pages]

    return render_to_response(template_name, RequestContext(request, {
        "products": products,
        "q": q,
        "total": total,
        "pages": pages,
        'show_first': 1 not in pages,
        'show_last': paginator.num_pages not in pages,
    }))
