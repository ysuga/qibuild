"Run the same command on each project"

import sys
import logging
import qibuild

def usage():
    "Specific usage"
    return """foreach -- COMMAND

Example:
toc foreach -- git reset --hard origin/v1.10.0

Use -- to seprate toc arguments from the arguments of the command.
(The -- is mandatory)

"""
def configure_parser(parser):
    """Configure parser for this action """
    qibuild.shell.toc_parser(parser)
    parser.add_argument("command", metavar="COMMAND",
        nargs="+")
    parser.add_argument("--ignore-errors", action="store_true",
        help="continue on error")

def do(args):
    """Main entry point"""
    toc = qibuild.toc.toc_open(args)
    logger = logging.getLogger(__name__)
    projects = toc.get_projects()
    for project in projects:
        logger.info("Running `%s` for %s", " ".join(args.command), project.name)
        src = project.get_src_dir()
        try:
            qibuild.command.check_call(args.command, cwd=src)
        except qibuild.command.CommandFailed, err:
            if args.ignore_errors:
                logger.error(str(err))
                continue
            else:
                raise


if __name__ == "__main__" :
    qibuild.shell.sub_command_main(sys.modules[__name__])
