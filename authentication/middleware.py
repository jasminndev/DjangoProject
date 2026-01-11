from django.utils import translation
from root.settings import LANGUAGES


class UserLanguageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        language = 'en'

        lang_header = request.META.get('HTTP_ACCEPT_LANGUAGE', '').split(',')[0].split('-')[0]

        if lang_header and lang_header in dict(LANGUAGES):
            language = lang_header

        if hasattr(request, 'user') and request.user.is_authenticated:
            user_lang = getattr(request.user, 'language', None)
            if user_lang and user_lang in dict(LANGUAGES):
                language = user_lang

        translation.activate(language)
        request.LANGUAGE_CODE = language

        response = self.get_response(request)

        translation.deactivate()

        return response