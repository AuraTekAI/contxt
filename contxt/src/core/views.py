from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse

def cache_test(request):
    """
    View to test and demonstrate cache functionality.

    This view checks if a specific key ('test_key') is present in the cache:
    - If the key is not present, it sets the key with a value of 'Cache test'.
    - If the key is present, it retrieves the value, sets an additional key ('test_key_2') with the same value,
      and retrieves the time-to-live (TTL) for the key 'test_key'.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response containing:
            - 'message': The value of the cache key 'test_key', or 'Cache not set' if the key was not set.
            - 'time_to_live': The time-to-live of the cache key 'test_key' if it exists, otherwise None.
    """
    payload = {'message': 'Cache not set'}

    time_to_live = None
    if not cache.get('test_key'):
        cache.set('test_key', 'Cache test')
    else:
        payload = cache.get('test_key')
        cache.set('test_key_2', 'Cache test')
        time_to_live = cache.ttl('test_key')

    return JsonResponse({'message': payload, 'time_to_live': time_to_live})

def test_home(request):
    """
    View to render the home page.

    This view renders the 'index.html' template.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered 'index.html' template.
    """
    return render(request, 'index.html', {})
