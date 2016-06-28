import re
from importlib import import_module

from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.conf import settings


def get_url_patterns(url_patterns_or_resolvers):
    """
    Extract all RegexURLPattern objects from a RegexURLResolver.
    """
    urls_patterns = []
    for item in url_patterns_or_resolvers:
        if isinstance(item, RegexURLPattern):
            urls_patterns.append(item)

        if isinstance(item, RegexURLResolver):
            urls_patterns.extend(get_url_patterns(item.url_patterns))
    return urls_patterns


def get_raw_urls(url_patterns):
    """
    Extract urls from a list of RegexURLPattern.

    The path parameters will still be in the resulting url. Here's is an example of response:
    [u'/caterers/<pk>', u'/vendors/<pk>']
    """
    views = extract_views_from_urlpatterns(url_patterns)
    template_urls = []

    for view in views:
        url = simplify_regex(view[1])
        template_urls.append(url)

    return template_urls


def clean_raw_urls(template_urls, default_value='1'):
    """
    Remove urls that we don't want to include.
    """
    result_urls = []
    pattern = re.compile(r'<\w+>')

    for url in template_urls:
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

    url_patterns = get_url_patterns(urlconfig_mod.urlpatterns)
    template_urls = get_raw_urls(url_patterns)
    endpoint_urls = clean_raw_urls(template_urls)
    return endpoint_urls
