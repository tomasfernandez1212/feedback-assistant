import unittest
import azure.functions as func
from unittest import mock

from HandleReviewChange import main


class TestHandleReviewChange(unittest.TestCase):
    def test_handle_review_change(self):
        req = mock.Mock(spec=func.HttpRequest)
        req.get_json.return_value = {"id": "YELP_9hHyzoRRlXr2tQFDXGSbmg"}  # type: ignore

        resp = main(req)
        self.assertEqual(
            resp.get_body(),
            b"Handling Review Change for ID: YELP_9hHyzoRRlXr2tQFDXGSbmg",
        )
