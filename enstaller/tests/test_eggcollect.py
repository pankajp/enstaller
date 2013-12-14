import os
import time
import unittest

import os.path as op

from egginst.main import EggInst
from egginst.tests.common import mkdtemp
from egginst.utils import makedirs

from enstaller.store.tests.common import DUMMY_EGG
from enstaller.eggcollect import EggCollection

# XXX: of course, installed metadata had to be different than the one in
# eggs...
def _dummy_installed_info(prefix):
    return {
        u'meta_dir': op.join(prefix, "EGG-INFO", "dummy"),
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
        u'key': u'dummy-1.0.0-1.egg',
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
            prefix = op.join(d, "env")

            _install_eggs_set([DUMMY_EGG], prefix)

            ec = EggCollection(prefix, False)

            info = ec.find(op.basename(DUMMY_EGG))
            self.assertEqual(info, _dummy_installed_info(prefix))

            info = ec.find("dummy-1.eggg")
            self.assertTrue(info is None)

    def test_query_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG
            prefix = op.join(d, "env")

            _install_eggs_set([egg], prefix)

            ec = EggCollection(prefix, False)

            index = list(ec.query(name="dummy"))
            self.assertEqual(len(index), 1)
            self.assertEqual(index[0],
                             (op.basename(egg), _dummy_installed_info(prefix)))

            index = list(ec.query(name="yummy"))
            self.assertEqual(index, [])

    def test_install_remove_simple(self):
        with mkdtemp() as d:
            egg = DUMMY_EGG
            egg_basename = op.basename(egg)
            prefix = op.join(d, "prefix")

            ec = EggCollection(prefix, False)
            self.assertTrue(ec.find(egg_basename) is None)

            ec.install(op.basename(egg), op.dirname(egg))
            self.assertTrue(ec.find(egg_basename) is not None)

            ec.remove(op.basename(egg))
            self.assertTrue(ec.find(egg_basename) is None)
