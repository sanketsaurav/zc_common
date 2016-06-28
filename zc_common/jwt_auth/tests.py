import re
from importlib import import_module

from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
from django.conf import settings


def get_service_endpoint_urls(urlconfig=None, default_value='1'):
    """
    This function finds all endpoint urls in a service.

    Args:
        urlconfig: A django url config module to use. Defaults to settings.ROOT_URLCONF
        default_value: A string value to replace all url parameters with

    Returns:
        A list of urls with path parameters (i.e. <pk>) replaced with default_value
    """
    if not urlconfig:
        urlconfig = getattr(settings, 'ROOT_URLCONF')

    try:
        urlconfig_mod = import_module(urlconfig)
    except Exception as ex:
        raise Exception(
            "Unable to import url config module. Url Config: {0}. Message: {1}".format(urlconfig, ex.message))

    extracted_views = extract_views_from_urlpatterns(urlconfig_mod.urlpatterns)
    views_regex_url_patterns = [item[1] for item in extracted_views]
    simplified_regex_url_patterns = [simplify_regex(pattern) for pattern in views_regex_url_patterns]

    # Strip out urls we don't need to test.
    result_urls = []
    pattern = re.compile(r'<\w+>')

    for url in simplified_regex_url_patterns:
        if url.find('<format>') != -1:
            continue

        if url == u'/':
            continue

        if url == u'/health':
            continue

        parameters = pattern.findall(url)
        for param in parameters:
            url = url.replace(param, default_value)

        result_urls.append(url)

    return result_urls