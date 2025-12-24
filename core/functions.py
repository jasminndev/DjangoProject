from http import HTTPStatus

from rest_framework.response import Response


def api_response(*, success: bool, message: str, data=None, status=HTTPStatus.OK):
    return Response(
        {
            "success": success,
            "message": message,
            "data": data
        },
        status=status
    )
