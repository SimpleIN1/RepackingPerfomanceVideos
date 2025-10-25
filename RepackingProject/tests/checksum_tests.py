import unittest

from RepackingProject.common.checksum import calculate_checksum, add_checksum_to_url


class ChecksumTests(unittest.TestCase):
    def test_calculate_checksum(self):
        shared_secret = "1234"
        string = "createa=1244&b=dfsdf"
        checksum = calculate_checksum(string, shared_secret)

        self.assertEqual(checksum, "8c3c3ace7519efd91c275ee36d853c58d2555034")

    def test_calculate_checksum_wrong_secret(self):
        shared_secret = "12342"
        string = "createa=1244&b=dfsdf"
        checksum = calculate_checksum(string, shared_secret)

        self.assertNotEqual(checksum, "8c3c3ace7519efd91c275ee36d853c58d2555034")

    def test_calculate_checksum_wrong_data(self):
        shared_secret = "1234"
        string = "createa=1244&b=dfsdf1"
        checksum = calculate_checksum(string, shared_secret)

        self.assertNotEqual(checksum, "8c3c3ace7519efd91c275ee36d853c58d2555034")

    def test_add_checksum(self):
        url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings"

        res = add_checksum_to_url(url, "1245")
        checksum_url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings?checksum=97c201d9b787363d2d29328eeb91c1ea3ed70189"
        self.assertEqual(res, checksum_url)

    def test_add_checksum_with_checksum(self):
        url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings?checksum=d874f371f65e13c511f73653a6f1b0cac5fd"

        res = add_checksum_to_url(url, "1245")
        checksum_url = "https://vcs-3.ict.sbras.ru/bigbluebutton/api/getRecordings?checksum=97c201d9b787363d2d29328eeb91c1ea3ed70189"
        self.assertEqual(res, checksum_url)

    def test_add_checksum_incorrect_url(self):
        url = ""
        res = add_checksum_to_url(url, "1245")
        self.assertFalse(res)