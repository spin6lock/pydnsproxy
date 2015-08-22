#encoding:utf8
from cache import memorized_domain
import unittest

class TestCacheClass(unittest.TestCase):
    def test_extract_ttl(self):
        def foo():
            pass
        m = memorized_domain(foo)
        with open("dns_resp", "r") as fin:
            data = fin.read()
        self.assertTrue(m.extract_ttl(data)==56)

if __name__ == "__main__":
    unittest.main()
