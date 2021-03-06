## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Automatic testing for qibuild

"""


import os
import re
import sys
import difflib

import unittest
import qibuild
import qibuild


try:
    import argparse
except ImportError:
    from qibuild.external import argparse


class QiBuildTestCase(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath(os.path.dirname(__file__))
        self.parser = argparse.ArgumentParser()
        qibuild.parsers.toc_parser(self.parser)
        qibuild.parsers.build_parser(self.parser)
        self.args = self.parser.parse_args([])
        if os.environ.get("DEBUG"):
            self.args.verbose = True
        if os.environ.get("PDB"):
            self.args.pdb = True
        self.args.work_tree = self.test_dir
        # Run qibuild clean
        self._run_action('clean', '-f')

    def _run_action(self, action, *args):
        qibuild.run_action("qibuild.actions.%s" % action, args,
            forward_args=self.args)

    def test_configure(self):
        self._run_action("configure", "world")

    def test_make(self):
        self._run_action("configure", "hello")
        self._run_action("make", "hello")

    def test_make_without_configure(self):
        self.assertRaises(Exception, self._run_action, "make", "hello")

    def test_install(self):
        self._run_action("configure", "hello")
        self._run_action("make", "hello")
        self._run_action("install", "hello", "/tmp")

    def test_ctest(self):
        self._run_action("configure", "hello")
        self._run_action("make", "hello")
        self._run_action("test", "hello")

    def test_package(self):
        self._run_action("package", "world")

    @unittest.skip("Bug still not fixed in qibuild/uselib.cmake ...")
    def test_preserve_cache(self):
        # If cache changes when runnning cmake .. after
        # qibuild configure, then you have two problems:
        #     * every target will alway be seen has out of date
        #     * chances are some list vars contains more element,
        #       so perf will decrease each time you run cmake ..
        # Since some IDE automatically run cmake .. (qtcreator,
        # visual studio, for instance), this will lead to
        # performance issues
        self._run_action("status")
        self._run_action("configure", "foo")
        toc = qibuild.toc.toc_open(self.test_dir, args=self.args)
        build_folder_name = toc.build_folder_name
        foo_src = os.path.join(self.test_dir, "foo")
        build_dir = os.path.join(foo_src, "build-%s" % build_folder_name)
        cmake_cache = os.path.join(build_dir, "CMakeCache.txt")

        # Read cache and check that DEPENDS value are here
        cache = qibuild.cmake.read_cmake_cache(cmake_cache)

        self.assertEquals(cache["EGGS_DEPENDS"], "spam")
        self.assertEquals(cache["BAR_DEPENDS"] , "eggs;spam")

        # run cmake .. once and store contents of cache:
        qibuild.command.call(["cmake", ".."], cwd=build_dir)
        before = ""
        with open(cmake_cache, "r") as fp:
            before = fp.readlines()

        # run cmake .. twice
        qibuild.command.call(["cmake", ".."], cwd=build_dir)
        after = ""
        with open(cmake_cache, "r") as fp:
            after = fp.readlines()

        diff = ""
        for line in difflib.unified_diff(before, after, fromfile='before', tofile='after'):
            diff += line

        self.assertEquals(diff, "", "Diff non empty\n%s" % diff)


if __name__ == "__main__":
    unittest.main()
