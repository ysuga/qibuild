## Copyright (c) 2012 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.

""" Common filesystem operations """

# Mostly wrappers around somehow strange-behaving
# shutil functions ...

import os
import sys
import time
import errno
import stat
import shutil
import tempfile
import logging
import subprocess

LOGGER = logging.getLogger("buildtool.sh")

def mkdir(dest_dir, recursive=False):
    """ Recursive mkdir (do not fail if file exists) """
    try:
        if recursive:
            os.makedirs(dest_dir)
        else:
            os.mkdir(dest_dir)
    except OSError, e:
        if e.errno == 17:
            # Directory already exists -> we don't care
            pass
        else:
            raise

#pylint: disable-msg=C0103
def ln(src, dst, symlink=True):
    """ ln (do not fail if file exists) """
    try:
        if symlink:
            os.symlink(src, dst)
        else:
            raise NotImplementedError
    except OSError, e:
        if e.errno == 17:
            pass
        else:
            raise

def configure_file(in_path, out_path, copy_only=False, *args, **kwargs):
    """Configure a file.
    :param in_path: input file
    :parm out_path: output file

    The out_path needs not to exist, missing leading directories will
    be created if necessary.

    If copy_only is True, the contents will be copied "as is".

    If not, we will use the args and kwargs parameter as in::

        in_content.format(*args, **kwargs)

    """
    mkdir(os.path.dirname(os.path.abspath(out_path)), recursive=True)
    with open(in_path, "r") as in_file:
        in_content = in_file.read()
        if copy_only:
            out_content = in_content
        else:
            out_content = in_content.format(*args, **kwargs)
        with open(out_path, "w") as out_file:
            out_file.write(out_content)

def _copy_link(src, dest, quiet):
    if not os.path.islink(src):
        raise Exception("%s is not a link!" % src)

    target = os.readlink(src)
        #remove existing stuff
    if os.path.lexists(dest):
        rm(dest)
    if sys.stdout.isatty() and not quiet:
        print "-- Installing %s -> %s" % (dest, target)
    os.symlink(target, dest)


def _handle_dirs(src, dest, root, directories, filter_fun, quiet):
    """ Helper function used by install()

    """
    rel_root = os.path.relpath(root, src)
    # To avoid filering './' stuff
    if rel_root == ".":
        rel_root = ""
    new_root = os.path.join(dest, rel_root)

    for directory in directories:
        to_filter = os.path.join(rel_root, directory)
        if not filter_fun(to_filter):
            continue
        dsrc  = os.path.join(root, directory)
        ddest = os.path.join(new_root, directory)

        if os.path.islink(dsrc):
            _copy_link(dsrc, ddest, quiet)
        else:
            if os.path.lexists(ddest) and not os.path.isdir(ddest):
                raise Exception("Expecting a directory but found a file: %s" % ddest)
            mkdir(ddest, recursive=True)

def _handle_files(src, dest, root, files, filter_fun, quiet):
    """ Helper function used by install()

    """
    rel_root = os.path.relpath(root, src)
    new_root = os.path.join(dest, rel_root)

    for f in files:
        if not filter_fun(os.path.join(rel_root, f)):
            continue
        fsrc  = os.path.join(root, f)
        fdest = os.path.join(new_root, f)
        if os.path.islink(fsrc):
            mkdir(new_root, recursive=True)
            _copy_link(fsrc, fdest, quiet)
        else:
            if os.path.lexists(fdest) and os.path.isdir(fdest):
                raise Exception("Expecting a file but found a directory: %s" % fdest)
            if sys.stdout.isatty() and not quiet:
                print "-- Installing %s" % fdest
            mkdir(new_root, recursive=True)
            # We do not want to fail if dest exists but is read only
            # (following what `install` does, but not what `cp` does)
            rm(fdest)
            shutil.copy(fsrc, fdest)


def install(src, dest, filter_fun=None, quiet=False):
    """Install a directory to a destination.

    If filter_fun is not None, then the file will only be
    installed if filter_fun(relative/path/to/file) returns
    True.

    Few notes: rewriting ``cp`` or ``install`` is a hard problem.
    This version will happily erase whatever is inside dest,
    (even it the dest is readonly, dest will be erased before being
    written) and it won't complain if dest does not exists (missing
    directories will simply be created)

    This function will preserve relative symlinks between directories,
    used for instance in Mac frameworks::

        |__ Versions
            |__ Current  -> 4.0
            |__ 4        -> 4.0
            |__ 4.0


    """
    # FIXME: add a `safe mode` ala install?
    if not os.path.exists(src):
        mess = "Could not install '%s' to '%s'\n" % (src, dest)
        mess += '%s does not exist' % src
        raise Exception(mess)

    src  = to_native_path(src)
    dest = to_native_path(dest)
    LOGGER.debug("Installing %s -> %s", src, dest)
    #pylint: disable-msg=E0102
    # (function IS already defined, that's the point!)
    if filter_fun is None:
        def filter_fun(_unused):
            return True

    if os.path.isdir(src):
        for (root, dirs, files) in os.walk(src):
            _handle_dirs (src, dest, root, dirs,  filter_fun, quiet)
            _handle_files(src, dest, root, files, filter_fun, quiet)
    else:
        # Emulate posix `install' behavior:
        # if dest is a dir, install in the directory, else
        # simply copy the file.
        if os.path.isdir(dest):
            dest = os.path.join(dest, os.path.basename(src))
        mkdir(os.path.dirname(dest), recursive=True)
        if sys.stdout.isatty() and not quiet:
            print "-- Installing %s" % dest
        # We do not want to fail if dest exists but is read only
        # (following what `install` does, but not what `cp` does)
        rm(dest)
        shutil.copy(src, dest)

def rm(name):
    """This one can take a file or a directory.
    Contrary to shutil.remove or os.remove, it:

    * won't fail if the directory does not exists
    * won't fail if the directory contains read-only files
    * won't fail if the file does not exists

    Please avoid using shutil.rmtree ...
    """
    if not os.path.lexists(name):
        return
    if os.path.isdir(name) and not os.path.islink(name):
        LOGGER.debug("Removing directory: %s", name)
        rmtree(name)
    else:
        LOGGER.debug("Removing %s", name)
        os.remove(name)

# Taken from gclient source code (BSD license)
def rmtree(path):
  """shutil.rmtree() on steroids.

  Recursively removes a directory, even if it's marked read-only.

  shutil.rmtree() doesn't work on Windows if any of the files or directories
  are read-only, which svn repositories and some .svn files are.  We need to
  be able to force the files to be writable (i.e., deletable) as we traverse
  the tree.

  Even with all this, Windows still sometimes fails to delete a file, citing
  a permission error (maybe something to do with antivirus scans or disk
  indexing).  The best suggestion any of the user forums had was to wait a
  bit and try again, so we do that too.  It's hand-waving, but sometimes it
  works. :/

  On POSIX systems, things are a little bit simpler.  The modes of the files
  to be deleted doesn't matter, only the modes of the directories containing
  them are significant.  As the directory tree is traversed, each directory
  has its mode set appropriately before descending into it.  This should
  result in the entire tree being removed, with the possible exception of
  ``path`` itself, because nothing attempts to change the mode of its parent.
  Doing so would be hazardous, as it's not a directory slated for removal.
  In the ordinary case, this is not a problem: for our purposes, the user
  will never lack write permission on ``path``'s parent.
  """
  if not os.path.exists(path):
    return

  if os.path.islink(path) or not os.path.isdir(path):
    raise Exception('Called rmtree(%s) in non-directory' % path)

  if sys.platform == 'win32':
    # Some people don't have the APIs installed. In that case we'll do without.
    win32api = None
    win32con = None
    try:
      # Unable to import 'XX'
      # pylint: disable=F0401
      import win32api, win32con
    except ImportError:
      pass
  else:
    # On POSIX systems, we need the x-bit set on the directory to access it,
    # the r-bit to see its contents, and the w-bit to remove files from it.
    # The actual modes of the files within the directory is irrelevant.
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

  def remove(func, subpath):
    if sys.platform == 'win32':
      os.chmod(subpath, stat.S_IWRITE)
      if win32api and win32con:
        win32api.SetFileAttributes(subpath, win32con.FILE_ATTRIBUTE_NORMAL)
    try:
      func(subpath)
    except OSError, e:
      if e.errno != errno.EACCES or sys.platform != 'win32':
        raise
      # Failed to delete, try again after a 100ms sleep.
      time.sleep(0.1)
      func(subpath)

  for fn in os.listdir(path):
    # If fullpath is a symbolic link that points to a directory, isdir will
    # be True, but we don't want to descend into that as a directory, we just
    # want to remove the link.  Check islink and treat links as ordinary files
    # would be treated regardless of what they reference.
    fullpath = os.path.join(path, fn)
    if os.path.islink(fullpath) or not os.path.isdir(fullpath):
      remove(os.remove, fullpath)
    else:
      # Recurse.
      rm(fullpath)

  remove(os.rmdir, path)

def mv(src, dest):
    """Move a file into a directory, but do not crash
    if dest/src exists

    """
    if os.path.isdir(dest):
        dest = os.path.join(dest, os.path.basename(src))
    if os.path.exists(dest):
        os.remove(dest)
    shutil.move(src, dest)


def ls_r(directory):
    """Returns a sorted list of all the files present in a diretory,
    relative to this directory.

    For instance, with::

        foo
        |__ eggs
        |    |__ c
        |    |__ d
        |__ empty
        |__ spam
            |__a
            |__b

    ls_r(foo) returns:
    ["eggs/c", "eggs/d", "empty/", "spam/a", "spam/b"]

    """
    res = list()
    for root, dirs, files in os.walk(directory):
        new_root = os.path.relpath(root, directory)
        if new_root == "." and not files:
            continue
        if new_root == "." and files:
            res.extend(files)
            continue
        if not files and not dirs:
            res.append(new_root + os.path.sep)
            continue
        for f in files:
            res.append(os.path.join(new_root, f))
    res.sort()
    return res

def which(program):
    """
    find program in the environment PATH
    :return: path to program if found, None otherwise
    """
    import warnings
    warnings.warn("qibuild.sh.which is deprecated, "
     "use qibuild.command.find_program instead")
    from qibuild.command import find_program
    return find_program(program)


def run(program, args):
    """ exec a process.

    * linux: this will call exec and replace the current process
    * windows: this will call spawn and wait till the end

    Example::

        run("python.exe", "toto.py")

    """
    real_args = [ program ]
    real_args.extend(args)

    if sys.platform.startswith("win32"):
        retcode = 0
        try:
            retcode = subprocess.call(real_args)
        except subprocess.CalledProcessError:
            print "problem when calling", program
            retcode = 2
        sys.exit(retcode)
        return

    os.execvp(program, real_args)

def to_posix_path(path):
    """
    Returns a POSIX path from a DOS path

    Useful because cmake *needs* POSIX paths.

    Guidelines:
        * always use os.path insternally
        * convert to POSIX path at the very last moment

    """
    res = os.path.expanduser(path)
    res = os.path.abspath(res)
    res = path.replace("\\", "/")
    return res

def to_dos_path(path):
    """Return a DOS path from a "windows with /" path.
    Useful because people sometimes use forward slash in
    environment variable, for instance
    """
    res = path.replace("/", "\\")
    return res

def to_native_path(path):
    """Return an absolute, native path from a path,
    (and all lower-case on case-insensitive filesystems)

    """
    path = os.path.expanduser(path)
    path = os.path.normcase(path)
    path = os.path.normpath(path)
    path = os.path.abspath(path)
    path = os.path.realpath(path)
    if sys.platform.startswith("win"):
        path = to_dos_path(path)
    return path


class TempDir:
    """This is a nice wrapper around tempfile module.

    Usage::

        with TempDir("foo-bar") as temp_dir:
            subdir = os.path.join(temp_dir, "subdir")
            do_foo(subdir)

    This piece of code makes sure that:

    * a temporary directory named temp_dir has been
      created (guaranteed to exist, be empty, and writeable)

    * the directory will be removed when the scope of
      temp_dir has ended unless an exception has occurred
      and DEBUG environment variable is set.

    """
    def __init__(self, name="tmp"):
        self._temp_dir = tempfile.mkdtemp(prefix=name+"-")

    def __enter__(self):
        return self._temp_dir

    def __exit__(self, type, value, tb):
        if os.environ.get("DEBUG"):
            if tb is not None:
                print "=="
                print "Not removing ", self._temp_dir
                print "=="
                return
        rm(self._temp_dir)




def is_runtime(filename):
    """ Filter function to only install runtime components of packages

    """
    # FIXME: this looks like a hack.
    # Maybe a user-generated MANIFEST at the root of the package path
    # would be better?

    basename = os.path.basename(filename)
    basedir  = filename.split(os.path.sep)[0]
    if filename.startswith("bin"):
        if sys.platform.startswith("win"):
            if filename.endswith(".exe"):
                return True
            if filename.endswith(".dll"):
                return True
            else:
                return False
        else:
            return True
    if filename.startswith("lib"):
        # exception for python:
        if "python" in filename and filename.endswith("Makefile"):
            return True
        # shared libraries
        shared_lib_ext = ""
        if sys.platform.startswith("win"):
            shared_lib_ext = ".dll"
        if sys.platform == "linux2":
            shared_lib_ext = ".so"
        if sys.platform == "darwing":
            shared_lib_ext = ".dylib"
        if shared_lib_ext in basename:
            return True
        # python
        if basename.endswith(".py"):
            return True
        if basename.endswith(".pyd"):
            return True
        else:
            return False
    if filename.startswith(os.path.join("share", "cmake")):
        return False
    if filename.startswith(os.path.join("share", "man")):
        return False
    if basedir == "share":
        return True
    if basedir == "include":
        # exception for python:
        if filename.endswith("pyconfig.h"):
            return True
        else:
            return False
    if basedir.endswith(".framework"):
        return True

    # True by default: better have too much stuff than
    # not enough
    return True
