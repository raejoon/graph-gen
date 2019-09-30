import unittest
import unittest.mock

import sleepwell
from constants import *


class TestSleepWell(unittest.TestCase):
    def setUp(self):
        self.node = sleepwell.SleepWellNode(0, None)
        self.node.neighbor_map = {1: INTERVAL//10, 2: INTERVAL//4,
                                  3: INTERVAL//2}
    
    def test_largest_gap(self):
        start, end = self.node.largest_gap()
        self.assertEqual(start, self.node.neighbor_map[3]) 
        self.assertEqual(end, self.node.neighbor_map[1])


    def test_target_share(self):
        self.assertEqual(self.node.target_share(), INTERVAL // 4)


    def test_adjust(self):
        with unittest.mock.patch("sleepwell.SleepWellNode.now") as mock_now:
            mock_now.return_value = 10 * INTERVAL + INTERVAL * 3 // 10
            interval = self.node.adjust()
            self.assertEqual(interval, INTERVAL + INTERVAL // 2)
