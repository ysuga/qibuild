"""Init a new toc workspace """

import os
import qibuild

def configure_parser(parser):
    """Configure parser for this action """
    qibuild.shell.toc_parser(parser)

def do(args):
    """Main entry point"""
    toc_dir = None
    if args.toc_work_tree:
        work_tree = args.toc_work_tree
    else:
        (toc_dir, work_tree) = qibuild.toc.path.get_dirs_from_env()
    if work_tree is None:
        work_tree = os.getcwd()
    if toc_dir is None:
        toc_dir = os.path.join(work_tree, ".toc")
    qibuild.toc.toc_create(work_tree, toc_dir)

if __name__ == "__main__" :
    import sys
    qibuild.shell.sub_command_main(sys.modules[__name__])