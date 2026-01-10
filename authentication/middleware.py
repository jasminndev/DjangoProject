from django.utils import translation

class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = 'en'

        if request.user.is_authenticated:
            language = getattr(request.user, 'language', 'en') or 'en'

        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)
        return response
