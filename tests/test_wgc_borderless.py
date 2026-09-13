import unittest
from unittest.mock import AsyncMock, patch

from core.managers import wgc_borderless
from core.managers.wgc_session_abi import WGCSessionABI


class BorderlessAccessTests(unittest.TestCase):

    def test_unsupported_windows_never_requests_access(self):
        with (
            patch.object(
                wgc_borderless,
                "is_borderless_capture_supported",
                return_value=False,
            ),
            patch.object(
                wgc_borderless,
                "_request_access",
                new_callable=AsyncMock,
            ) as request,
        ):
            self.assertFalse(
                wgc_borderless.request_borderless_capture_access()
            )

        request.assert_not_called()

    def test_access_is_enabled_only_when_windows_allows_it(self):
        with (
            patch.object(
                wgc_borderless,
                "is_borderless_capture_supported",
                return_value=True,
            ),
            patch.object(
                wgc_borderless,
                "_request_access",
                new_callable=AsyncMock,
                return_value=wgc_borderless.ACCESS_ALLOWED,
            ) as request,
        ):
            self.assertTrue(
                wgc_borderless.request_borderless_capture_access()
            )
            self.assertTrue(
                wgc_borderless.request_borderless_capture_access()
            )

        self.assertEqual(request.await_count, 2)

    def test_denied_access_keeps_the_capture_border(self):
        with (
            patch.object(
                wgc_borderless,
                "is_borderless_capture_supported",
                return_value=True,
            ),
            patch.object(
                wgc_borderless,
                "_request_access",
                new_callable=AsyncMock,
                return_value=2,
            ),
        ):
            self.assertFalse(
                wgc_borderless.request_borderless_capture_access()
            )

    def test_windows_11_build_boundary_controls_requirement(self):
        with patch.object(wgc_borderless.sys, "platform", "win32"):
            for build, expected in ((21999, False), (22000, True)):
                with (
                    self.subTest(build=build),
                    patch.object(
                        wgc_borderless.sys,
                        "getwindowsversion",
                        return_value=type(
                            "Version",
                            (),
                            {"build": build},
                        )(),
                    ),
                ):
                    self.assertEqual(
                        wgc_borderless.is_borderless_capture_required(),
                        expected,
                    )


class BorderlessSessionTests(unittest.TestCase):

    def test_session3_disables_the_border_and_is_released(self):
        manager = WGCSessionABI()
        manager.session = "session"

        with (
            patch.object(
                manager,
                "_query_border_session",
                return_value="session3",
            ),
            patch.object(
                manager,
                "_set_border_required",
                return_value=True,
            ) as setter,
            patch(
                "core.managers.wgc_session_abi.release_com"
            ) as release,
        ):
            self.assertTrue(manager.try_disable_border())

        setter.assert_called_once_with("session3", False)
        release.assert_called_once_with("session3")

    def test_missing_session3_falls_back_without_failure(self):
        manager = WGCSessionABI()
        manager.session = "session"

        with (
            patch.object(
                manager,
                "_query_border_session",
                return_value=None,
            ),
            patch(
                "core.managers.wgc_session_abi.release_com"
            ) as release,
        ):
            self.assertFalse(manager.try_disable_border())

        release.assert_not_called()


if __name__ == "__main__":
    unittest.main()
