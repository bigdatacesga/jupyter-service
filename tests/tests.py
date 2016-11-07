"""Tests for the paas service REST API"""
import unittest
import registry
from app import utils

ENDPOINT = 'http://consul:8500/v1/kv'


def suite():
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestProcessPool)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestAPI)
    return unittest.TestSuite([suite1, suite2])


class TestProcessPool(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_add_and_get_proc(self):
        pool = utils.ProcessPool()
        pool.add('javier', 'abc1234567890', 'XYZ')
        self.assertEqual(pool.get('javier', 'abc1234567890'), 'XYZ')

    def test_remove_proc(self):
        pool = utils.ProcessPool()
        pool.add('javier', 'abc1234567890', 'XYZ')
        pool.remove('javier', 'abc1234567890')
        self.assertEqual(pool.get('javier', 'abc1234567890'), None)

    def test_get_non_existant_proccess(self):
        pool = utils.ProcessPool()
        self.assertIsNone(pool.get('javier', 'abc1234567890'))

    def test_get_user_proccesses(self):
        pool = utils.ProcessPool()
        pool.add('javier', 'abc1234567890', 'XYZ')
        self.assertEqual(pool.from_user('javier'), {'abc1234567890': 'XYZ'})

    def test_get_all_proccesses(self):
        pool = utils.ProcessPool()
        pool.add('javier', 'session1', 'XYZ')
        pool.add('javier', 'session2', 'XYZ')
        pool.add('juan', 'session1', 'ABC')
        expected = {'javier': {'session1': 'XYZ', 'session2': 'XYZ'},
                    'juan': {'session1': 'ABC'}}
        self.assertEqual(pool.get_all(), expected)


class TestAPI(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass
