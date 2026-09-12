import unittest

from api import app as app_module


class EmailConfigTests(unittest.TestCase):
    def test_normalize_env_value_removes_whitespace(self):
        self.assertEqual(app_module.normalize_env_value("hqmc qgln bzxg kibx"), "hqmcqglnbzxgkibx")

    def test_has_email_config_accepts_real_values(self):
        self.assertTrue(
            app_module.has_email_config(
                "smtp.gmail.com",
                "587",
                "user@gmail.com",
                "app-password-with-spaces",
                "recipient@gmail.com",
            )
        )


if __name__ == "__main__":
    unittest.main()
