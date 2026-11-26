import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import unittest
from main import audit

def row(destination, gateway, interface="eth0", metric=100):
    return {"destination": destination, "gateway": gateway,
            "interface": interface, "metric": str(metric)}

class TestRouteTableAuditor(unittest.TestCase):
    def test_ok_route(self):
        r, _, default = audit([row("10.0.0.0/24", "0.0.0.0"),
                               row("0.0.0.0/0", "10.0.0.1")])
        self.assertEqual(r[1][1], "OK")
        self.assertTrue(default)

    def test_missing_default_route(self):
        _, _, default = audit([row("10.0.0.0/24", "0.0.0.0")])
        self.assertFalse(default)

    def test_duplicate_destination(self):
        r, _, _ = audit([row("172.16.0.0/16", "10.0.0.1"),
                         row("172.16.0.0/16", "192.168.1.1"),
                         row("10.0.0.0/24", "0.0.0.0")])
        self.assertEqual(r[0][1], "DUPLICATE")
        self.assertIn("2 time(s)", r[0][2])

    def test_unreachable_gateway(self):
        r, _, _ = audit([row("10.0.0.0/24", "0.0.0.0"),
                         row("203.0.113.0/24", "198.51.100.1")])
        self.assertEqual(r[0][1], "UNREACHABLE GATEWAY")

    def test_gateway_inside_connected_network_is_ok(self):
        r, _, _ = audit([row("10.0.0.0/24", "0.0.0.0"),
                         row("172.16.0.0/16", "10.0.0.1")])
        self.assertEqual(r[0][1], "OK")

    def test_on_link_gateway_is_connected(self):
        r, _, _ = audit([row("192.168.1.0/24", "on-link"),
                         row("172.16.0.0/16", "192.168.1.5")])
        self.assertEqual(r[0][1], "OK")

    def test_duplicate_comes_first(self):
        r, _, _ = audit([row("203.0.113.0/24", "198.51.100.1"),
                         row("172.16.0.0/16", "10.0.0.1"),
                         row("172.16.0.0/16", "10.0.0.2"),
                         row("10.0.0.0/24", "0.0.0.0")])
        self.assertEqual(r[0][1], "DUPLICATE")

    def test_invalid_row_is_skipped(self):
        r, skipped, _ = audit([row("not-a-network", "10.0.0.1"),
                               row("10.0.0.0/24", "0.0.0.0")])
        self.assertEqual((len(r), skipped), (1, 1))

    def test_empty_input(self):
        self.assertEqual(audit([]), ([], 0, False))
