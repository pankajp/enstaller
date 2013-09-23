import sys
import unittest

import mock

from egginst.scripts import get_executable

class TestScripts(unittest.TestCase):
    def test_get_executable(self):
        # FIXME: EggInst init overwrite egginst.scripts.executable. Need to
        # mock this until we remove that insanity
        with mock.patch("egginst.scripts.executable", sys.executable):
            executable = get_executable()
            self.assertEqual(executable, sys.executable)

            executable = get_executable(with_quotes=True)
            self.assertEqual(executable, "\"{0}\"".format(sys.executable))

        with mock.patch("egginst.scripts.on_win", "win32"):
            with mock.patch("egginst.scripts.executable", "python.exe"):
                executable = get_executable()
                self.assertEqual(executable, "python.exe")

            with mock.patch("egginst.scripts.executable", "pythonw.exe"):
                executable = get_executable()
                self.assertEqual(executable, "python.exe")

                executable = get_executable(pythonw=True)
                self.assertEqual(executable, "pythonw.exe")
