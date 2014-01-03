import os
import time
import unittest

import os.path as op

from egginst.main import EggInst
from egginst.tests.common import mkdtemp, DUMMY_EGG, NOSE_1_2_1, NOSE_1_3_0
from egginst.utils import makedirs

from enstaller.eggcollect import EggCollection, JoinedEggCollection

# XXX: of course, installed metadata had to be different than the one in
# eggs...
def _dummy_installed_info(prefix):
    return {
        u'meta_dir': os.path.join(prefix, "EGG-INFO", "dummy"),
        u'ctime': time.ctime(),
        u'name': u'dummy',
        u'platform': u'linux2',
        u'python': u'2.7',
        u'type': u'egg',
        u'osdist': u'RedHat_5',
        u'installed': True,
        u'hook': False,
        u'version': u'1.0.1',
        u'build': 1,
        u'key': u'dummy-1.0.1-1.egg',
        u'packages': [],
        u'arch': u'x86',
    }

def _install_eggs_set(eggs, prefix):
    makedirs(prefix)

    for egg in eggs:
        egginst = EggInst(egg, prefix)
        egginst.install()

class TestEggCollection(unittest.TestCase):
    def test_find_simple(self):
        with mkdtemp() as d:
            prefix = os.path.join(d, "env")

            _install_eggs_set([DUMMY_EGG], prefix)

            ec = EggCollection(prefix, False)

            info = ec.find(os.path.basename(DUMMY_EGG))
            self.assertEqual(info, _dummy_installed_info(prefix))

            info = ec.find("dummy-1.eggg")
            self.assertTrue(info is None)

    def test_query_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG
            prefix = os.path.join(d, "env")

            _install_eggs_set([egg], prefix)

            ec = EggCollection(prefix, False)

            index = list(ec.query(name="dummy"))
            self.assertEqual(len(index), 1)
            self.assertEqual(index[0],
                             (os.path.basename(egg), _dummy_installed_info(prefix)))

            index = list(ec.query(name="yummy"))
            self.assertEqual(index, [])

    def test_install_remove_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG
            egg_basename = os.path.basename(egg)
            prefix = os.path.join(d, "prefix")

            ec = EggCollection(prefix, False)
            self.assertTrue(ec.find(egg_basename) is None)

            ec.install(os.path.basename(egg), os.path.dirname(egg))
            self.assertTrue(ec.find(egg_basename) is not None)

            ec.remove(os.path.basename(egg))
            self.assertTrue(ec.find(egg_basename) is None)

def _create_joined_collection(prefixes, eggs):
    ecs = []
    for i, prefix in enumerate(prefixes):
        ec = EggCollection(prefix, False)
        for egg in eggs[i]:
            ec.install(os.path.basename(egg), os.path.dirname(egg))
        ecs.append(ec)
    return JoinedEggCollection(ecs)

class TestJoinedEggCollection(unittest.TestCase):
    def test_find_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG
            egg_basename = os.path.basename(egg)
            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[egg], [egg]]
            store = _create_joined_collection((prefix0, prefix1), eggs)

            info = store.find(egg_basename)
            self.assertEqual(info, _dummy_installed_info(prefix0))
            self.assertNotEqual(info, _dummy_installed_info(prefix1))

    def test_query_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG

            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[egg], [egg]]
            store = _create_joined_collection((prefix0, prefix1), eggs)

            info = list(store.query(name="dummy"))

            self.assertEqual(len(info), 1)
            entry = info[0]
            self.assertEqual(entry[0], os.path.basename(egg))
            self.assertEqual(entry[1], _dummy_installed_info(prefix0))

    def test_query_precedence_lower_version_on_top(self):
        """
        Check that query returns the egg in highest priority collection
        when an egg exists in multiple collections.
        """
        with mkdtemp() as d:
            nose_1_2_1 = NOSE_1_2_1
            nose_1_3_0 = NOSE_1_3_0

            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[nose_1_2_1], [nose_1_3_0]]
            store = _create_joined_collection((prefix0, prefix1), eggs)

            info = list(store.query(name="nose"))

            self.assertEqual(len(info), 1)
            entry = info[0]
            self.assertEqual(entry[0], os.path.basename(nose_1_2_1))
            self.assertEqual(entry[1]["version"], "1.2.1")

    def test_query_precedence_higher_version_on_top(self):
        with mkdtemp() as d:
            nose_1_2_1 = NOSE_1_2_1
            nose_1_3_0 = NOSE_1_3_0

            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[nose_1_3_0], [nose_1_2_1]]
            store = _create_joined_collection((prefix0, prefix1), eggs)

            info = list(store.query(name="nose"))

            self.assertEqual(len(info), 1)
            entry = info[0]
            self.assertEqual(entry[0], os.path.basename(nose_1_3_0))
            self.assertEqual(entry[1]["version"], "1.3.0")

    def test_install_simple(self):
        """
        Ensure egg is installed in highest priority prefix.
        """
        with mkdtemp() as d:
            egg = DUMMY_EGG
            egg_basename = os.path.basename(egg)

            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[], []]

            store = _create_joined_collection((prefix0, prefix1), eggs)
            store.install(os.path.basename(egg), os.path.dirname(egg))

            ec0 = EggCollection(prefix0, False)
            ec1 = EggCollection(prefix1, False)

            self.assertTrue(ec0.find(egg_basename) is not None)
            self.assertTrue(ec1.find(egg_basename) is None)

    def test_remove_simple(self):
        """
        Ensure egg is removed only highest priority prefix.
        """
        with mkdtemp() as d:
            egg = DUMMY_EGG
            egg_basename = os.path.basename(egg)

            prefix0 = os.path.join(d, "prefix0")
            prefix1 = os.path.join(d, "prefix1")

            eggs = [[egg], []]

            store = _create_joined_collection((prefix0, prefix1), eggs)

            ec0 = EggCollection(prefix0, False)
            ec1 = EggCollection(prefix1, False)

            self.assertTrue(ec0.find(egg_basename) is not None)
            self.assertTrue(ec1.find(egg_basename) is None)

            store.remove(egg_basename)

            self.assertTrue(ec0.find(egg_basename) is None)
            self.assertTrue(ec1.find(egg_basename) is None)
