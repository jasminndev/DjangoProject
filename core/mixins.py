from django.utils import translation


class LanguageMixin:
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        translation.deactivate()

        if request.user.is_authenticated:
            user_lang = getattr(request.user, 'language', 'en')
            translation.activate(user_lang)
        else:
            translation.activate('en')

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        translation.deactivate()
        return response
