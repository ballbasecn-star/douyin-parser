"""发布版本号相关的最小回归测试。"""

import importlib
import os
import unittest

from app.infra import settings
from app.services import system_service


class ReleaseVersionTests(unittest.TestCase):
    def test_health_payload_uses_release_version_when_present(self):
        previous_release = os.environ.get("APP_RELEASE_VERSION")
        try:
            os.environ["APP_RELEASE_VERSION"] = "v1.0.0-20260321-abcdef1"
            importlib.reload(settings)
            importlib.reload(system_service)

            payload = system_service.get_health_payload()

            self.assertEqual(payload["version"], "v1.0.0-20260321-abcdef1")
            self.assertEqual(payload["app_version"], "1.0.0")
            self.assertEqual(payload["release_version"], "v1.0.0-20260321-abcdef1")
        finally:
            if previous_release is None:
                os.environ.pop("APP_RELEASE_VERSION", None)
            else:
                os.environ["APP_RELEASE_VERSION"] = previous_release
            importlib.reload(settings)
            importlib.reload(system_service)
