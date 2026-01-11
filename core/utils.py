import logging

from django.utils.deprecation import MiddlewareMixin

requests_logger = logging.getLogger("requests_logger")


class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = self.get_client_ip(request)
        request._log_client_ip = ip
        requests_logger.info(
            f"Request received: {request.method} {request.get_full_path()}",
            extra={
                "client_ip": ip,
                "method": request.method,
                "path": request.get_full_path(),
            }
        )

    def process_response(self, request, response):
        ip = getattr(request, "_log_client_ip", "unknown")
        requests_logger.info(
            f"Response sent: status={response.status_code}",
            extra={
                "client_ip": ip,
                "method": request.method,
                "path": request.get_full_path(),
            }
        )
        return response

    def process_exception(self, request, exception):
        ip = getattr(request, "_log_client_ip", "unknown")
        requests_logger.error(
            f"Exception occurred: {str(exception)}",
            extra={
                "client_ip": ip,
                "method": request.method,
                "path": request.get_full_path(),
            }
        )

    @staticmethod
    def get_client_ip(request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
