import unittest
from unittest.mock import patch

from app.cli.cookie_commands import handle_cookie_command
from app.cli.main import main
from app.cli.parse_commands import handle_parse_command


class CliCommandTests(unittest.TestCase):
    @patch("app.cli.parse_commands.parse_video")
    @patch("builtins.print")
    def test_handle_parse_command_calls_parse_video(self, _mock_print, mock_parse_video):
        mock_result = unittest.mock.Mock()
        mock_result.format_output.return_value = "ok"
        mock_parse_video.return_value = mock_result

        exit_code = handle_parse_command(["--no-transcript", "https://www.douyin.com/video/123"])

        self.assertEqual(exit_code, 0)
        mock_parse_video.assert_called_once_with(
            share_text="https://www.douyin.com/video/123",
            service_url=None,
            enable_transcript=False,
            use_cloud=False,
            cloud_provider="groq",
            model_size="large-v3",
            cloud_api_key=None,
            enable_analysis=False,
        )

    @patch("app.cli.cookie_commands.get_cookie_manager")
    @patch("builtins.print")
    def test_handle_cookie_command_show_outputs_status(self, mock_print, mock_get_cookie_manager):
        manager = mock_get_cookie_manager.return_value
        manager.get_cookie_info.return_value = {
            "exists": True,
            "source": "manual",
            "timestamp": "2026-03-21T20:00:00",
            "cookie_length": 12,
        }
        manager.get_cookie.return_value = "sid=abcd1234"

        exit_code = handle_cookie_command(["show"])

        self.assertEqual(exit_code, 0)
        self.assertTrue(mock_print.called)

    @patch("app.cli.main.handle_parse_command", return_value=0)
    def test_main_routes_empty_args_to_parse(self, mock_handle_parse_command):
        exit_code = main([])

        self.assertEqual(exit_code, 0)
        mock_handle_parse_command.assert_called_once_with([])

    @patch("app.cli.main.handle_cookie_command", return_value=0)
    def test_main_routes_cookie_subcommand(self, mock_handle_cookie_command):
        exit_code = main(["cookie", "show"])

        self.assertEqual(exit_code, 0)
        mock_handle_cookie_command.assert_called_once_with(["show"])


if __name__ == "__main__":
    unittest.main()
