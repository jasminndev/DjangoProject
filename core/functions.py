from http import HTTPStatus

from rest_framework.response import Response


def api_response(*, success: bool, message: str, data=None, status=HTTPStatus.OK, error_code: str = None):
    response_data = {
        "success": success,
        "message": message,
        "data": data
    }

    if not success and error_code:
        response_data["error_code"] = error_code

    return Response(response_data, status=status)

