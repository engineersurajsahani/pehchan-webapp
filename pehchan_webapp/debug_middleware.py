import traceback
from django.http import HttpResponse

class GlobalExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        return HttpResponse(
            f"GLOBAL CRITICAL ERROR: {str(exception)}\n\nTraceback:\n{traceback.format_exc()}",
            content_type="text/plain",
            status=500
        )
