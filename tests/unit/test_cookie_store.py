import tempfile
import unittest

from app.infra.cookie_store import CookieManager
from douyin.cookie_manager import CookieManager as LegacyCookieManager


class CookieStoreTestCase(unittest.TestCase):
    def test_cookie_manager_can_save_and_load_cookie(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = CookieManager(cookie_dir=temp_dir)

            manager.save_cookie("sid=abc123", source="unit-test")
            info = manager.get_cookie_info()

            self.assertEqual(manager.get_cookie(), "sid=abc123")
            self.assertEqual(
                info,
                {
                    "exists": True,
                    "source": "unit-test",
                    "timestamp": info["timestamp"],
                    "cookie_length": 10,
                },
            )

    def test_legacy_cookie_manager_import_still_points_to_new_impl(self):
        self.assertIs(LegacyCookieManager, CookieManager)


if __name__ == "__main__":
    unittest.main()
