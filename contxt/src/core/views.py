from django.shortcuts import render
from django.core.cache import cache
from django.http import JsonResponse


def cache_test(request):
    payload = {'message' : 'Cache not set'}

    time_to_live = None
    if not cache.get('test_key'):
        cache.set('test_key', 'Cache test')
    else:
        payload = cache.get('test_key')
        cache.set(f'test_key_2', 'Cache test')
        time_to_live = cache.ttl('test_key')
    payload=payload

    return JsonResponse({'message' : payload, 'time_to_live' : time_to_live})

def test_home(request):
    return render(request, 'index.html', {})
