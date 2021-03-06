## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

"""Automatic testing for the Toc object

"""

import os
import tempfile
import unittest

import qibuild
import qitoolchain

class TocTestCase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="test-feed")
        qibuild.sh.mkdir(os.path.join(self.tmp, "qi"))
        self.world_package = qitoolchain.Package("world", "package/world")
        self.world_project = qibuild.project.Project("world", "src/world")
        self.hello_project = qibuild.project.Project("hello", "src/hello")
        self.world_project.build_directory = "src/world/build"
        self.hello_project.build_directory = "src/hello/build"
        self.hello_project.depends = ["world"]
        self.toc = qibuild.toc.Toc(self.tmp)

    def test_src_deps(self):
        self.toc.projects = [self.hello_project, self.world_project]
        hello_sdk_dirs = self.toc.get_sdk_dirs("hello")
        self.assertEquals(hello_sdk_dirs, ["src/world/build/sdk"])

    def test_package_wins_on_project(self):
        self.toc.projects = [self.hello_project, self.world_project]
        self.toc.packages = [self.world_package]
        hello_sdk_dirs = self.toc.get_sdk_dirs("hello")
        self.assertEquals(hello_sdk_dirs, list())

    def test_package_wins_on_project_unless_user_asked(self):
        self.toc.projects = [self.hello_project, self.world_project]
        self.toc.packages = [self.world_package]
        self.toc.active_projects = ["world", "hello"]
        hello_sdk_dirs = self.toc.get_sdk_dirs("hello")
        self.assertEquals(hello_sdk_dirs, ["src/world/build/sdk"])
        workd_sdk_dirs = self.toc.get_sdk_dirs("world")
        self.assertEquals(workd_sdk_dirs, list())


    def tearDown(self):
        qibuild.sh.rm(self.tmp)



if __name__ == "__main__":
    unittest.main()

