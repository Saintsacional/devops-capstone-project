# tests/test_error_handlers.py
import unittest

# Import the real app and handlers from your package
from service import app as real_app
from service.common import error_handlers as handlers
from service.common import status
from service.models import DataValidationError


class TestErrorHandlers(unittest.TestCase):
    """Covers service/common/error_handlers.py"""

    def setUp(self):
        # Use the real app so logger and config wiring is exercised
        self.app = real_app
        self.app.testing = True
        self.client = self.app.test_client()

    def _assert_json(
        self, resp, expected_status, expected_error, expected_message_substr
    ):
        self.assertEqual(resp[1], expected_status)
        payload = resp[0].get_json()
        self.assertEqual(payload["status"], expected_status)
        self.assertEqual(payload["error"], expected_error)
        # message comes from str(error); we assert it contains our string
        self.assertIn(expected_message_substr, payload["message"])

    def test_400_bad_request_handler(self):
        msg = "invalid payload provided"
        resp = handlers.bad_request(ValueError(msg))
        self._assert_json(
            resp,
            status.HTTP_400_BAD_REQUEST,
            "Bad Request",
            "invalid payload provided",
        )

    def test_400_datavalidation_error_handler(self):
        # DataValidationError should be routed to bad_request()
        msg = "field x is required"
        resp = handlers.request_validation_error(DataValidationError(msg))
        self._assert_json(
            resp,
            status.HTTP_400_BAD_REQUEST,
            "Bad Request",
            "field x is required",
        )

    def test_404_not_found_handler(self):
        msg = "resource not found: /does-not-exist"
        resp = handlers.not_found(RuntimeError(msg))
        self._assert_json(
            resp,
            status.HTTP_404_NOT_FOUND,
            "Not Found",
            "resource not found",
        )

    def test_405_method_not_allowed_handler(self):
        msg = "method PUT not allowed"
        resp = handlers.method_not_supported(RuntimeError(msg))
        self._assert_json(
            resp,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            "Method not Allowed",
            "method PUT not allowed",
        )

    def test_415_unsupported_media_type_handler(self):
        msg = "Content-Type: text/plain is not supported"
        resp = handlers.mediatype_not_supported(RuntimeError(msg))
        self._assert_json(
            resp,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Unsupported media type",
            "text/plain is not supported",
        )

    def test_500_internal_server_error_handler(self):
        msg = "unexpected failure in service"
        resp = handlers.internal_server_error(RuntimeError(msg))
        self._assert_json(
            resp,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Internal Server Error",
            "unexpected failure in service",
        )

    def test_integration_unknown_route_404(self):
        # Bonus: hit a guaranteed-unknown URI to ensure 404 path engages
        rv = self.client.get("/__definitely_unknown__")
        # If your app has its own 404 handler registered (it does), this will
        # exercise that code path as well.
        self.assertEqual(rv.status_code, status.HTTP_404_NOT_FOUND)
        payload = rv.get_json()
        # message is a Werkzeug-generated message; ensure keys are present
        self.assertIn("status", payload)
        self.assertEqual(payload["status"], status.HTTP_404_NOT_FOUND)
        self.assertEqual(payload["error"], "Not Found")


if __name__ == "__main__":
    unittest.main()
