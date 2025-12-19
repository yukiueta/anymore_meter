from django.utils.deprecation import MiddlewareMixin

class AllowXFrameOptionsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['X-Frame-Options'] = 'ALLOWALL'
        return response
