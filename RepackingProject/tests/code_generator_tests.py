import unittest

from RepackingProject.common.code_generator import generate_code


class CodeGeneratorTests(unittest.TestCase):
    def test_generate_code(self):
        code = generate_code()

        self.assertEqual(type(code), str)
        self.assertTrue(code.isdigit())

        code = int(code)
        self.assertGreater(code, 0)
        self.assertLess(code, 100000)
