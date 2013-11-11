import unittest

from enstaller.main import main

class TestEnstallerMain(unittest.TestCase):
    def test_print_version(self):
        # XXX: this is lousy test: we'd like to at least ensure we're printing
        # the correct version, but capturing the stdout is a bit tricky. Once
        # we replace print by proper logging, we should be able to do better.
        try:
            main(["--version"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)

    def test_help_runs_and_exits_correctly(self):
        try:
            main(["--help"])
        except SystemExit as e:
            self.assertEqual(e.code, 0)
