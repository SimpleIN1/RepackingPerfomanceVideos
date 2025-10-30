
import unittest

from RepackingProject.common.manage_datetime import current_year


class DatetimeTests(unittest.TestCase):
    def test_calculate_checksum(self):
        year = 2025
        date_year = current_year()

        self.assertEqual(date_year, year)
