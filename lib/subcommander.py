#!/usr/bin/python3
# Description: Runs subcommands

'''subcommander.py

Invokes subcommands arranged into a directory hierarchy.

Usage: create a symlink to this file named for your top-level tool e.g.
"mytool", then place scripts to become subcommands in ~/usr/lib/mytool/

See README.md for details.

'''
#
# Copyright 2014  Michael F. Lamb <http://datagrok.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# License: GPLv3+ http://www.gnu.org/licenses/gpl.html
#

import logging
import os
import subprocess
import sys
import textwrap
import warnings

logger = logging.getLogger(os.path.basename(sys.argv[0]))


def format_msg(s):
    """Helper that unindents and unwraps multiline docstrings."""
    return textwrap.fill(textwrap.dedent(s).strip())


def format_script(s):
    """Helper that unindents multiline docstrings."""
    return textwrap.dedent(s).strip() + '\n'


class SubcommanderUserError(Exception):
    """Subclasses of this class will not display a python traceback when thrown
    to the user.

    """
    def __str__(self):
        if self.filename:
            return format_msg("%s: %s" % (self.strerror, self.filename))
        else:
            return format_msg(self.strerror)


class CalledDirectlyError(SubcommanderUserError, EnvironmentError):
    def __init__(self):
        super(CalledDirectlyError, self).__init__(
            1, """
            Subcommander is an abstraction that is not meant to be run under
            its own name. Instead, create a symlink to it, with a different
            name. And read the instructions.""")


class SubcommandDirectoryNotConfiguredError(SubcommanderUserError, EnvironmentError):
    def __init__(self, exec_path_envname, rcfile):
        super(SubcommandDirectoryNotConfiguredError, self).__init__(
            6, """
            Could not find %s set in the environment. This should specify the
            path to subcommands. Recommend adding it to %s.""" % (
                exec_path_envname, rcfile))


class SubcommandDirectoryMissingError(SubcommanderUserError, EnvironmentError):
    def __init__(self, exec_path):
        super(SubcommandDirectoryMissingError, self).__init__(
            4, """
            Subcommands directory does not exist. Place executable files here
            to enable them as sub-commands""",
            exec_path)


class NoCommandSpecifiedError(SubcommanderUserError, EnvironmentError):
    def __init__(self):
        super(NoCommandSpecifiedError, self).__init__(
            2, "No COMMAND specified.")


class UnknownSubcommandError(SubcommanderUserError, EnvironmentError):
    def __init__(self, command):
        message = "Not a known COMMAND for %r" % os.environ['SC_COMMAND']
        if len(command) > 1:
            message = """
            Complete command sequence must precede options and other
            arguments. """ + message

        super(UnknownSubcommandError, self).__init__(
            3, message, command[0])


class ConfigFileNotExecutableError(SubcommanderUserError, EnvironmentError):
    def __init__(self, configfile):
        super(ConfigFileNotExecutableError, self).__init__(
            5, "Configuration file is not executable",
            configfile)


def create_rc_file(rcfile, exec_path_envname):
    """The rcfile does not exist, so create one prepopulated with some helpful
    comments.

    """
    logger.warn("Creating rcfile %s." % rcfile)
    with open(rcfile, 'w') as fp:
        fp.write(format_script("""
            #!/bin/sh

            # This file is executed by '%(SC_ARGV0)s' every time you run a
            # '%(SC_ARGV0)s' subcommand. You can edit this script, or replace it
            # with your own executable script or compiled program, so long as
            # you take care to exec() the command passed in as arguments, as is
            # done below.

            # This line sets %(exec_path_envname)s to ~/usr/lib/%(SC_ARGV0)s
            # unless it is overridden in the environment.
            export %(exec_path_envname)s="${%(exec_path_envname)s:-~/usr/lib/%(SC_ARGV0)s}"

            # If you have hooks to execute or customizations to make to the
            # environment, you may do so here.

            # The following line must be present for '%(SC_ARGV0)s' to function.
            # It ends the script; any lines after it will never be reached.
            if [ -x "$%(exec_path_envname)s/.apply_context" ]
            then exec "$%(exec_path_envname)s/.apply_context" "$0"
            else exec "$@"
            fi
            """ % {
                'exec_path_envname': exec_path_envname,
                'SC_ARGV0': os.environ['SC_ARGV0'],
            }))
        os.fchmod(fp.fileno(), 0755)


def get_exec_path(exec_path_envname, rcfile):
    """Return the path where subcommands may be found.

    Raises exceptions if the path is unconfigured or nonexistent.

    """
    try:
        exec_path = os.environ[exec_path_envname]
    except KeyError:
        raise SubcommandDirectoryNotConfiguredError(exec_path_envname, rcfile)

    exec_path = os.path.expanduser(exec_path)

    if not os.path.isdir(exec_path):
        raise SubcommandDirectoryMissingError(exec_path)

    return exec_path


def show_help(exec_path):
    """If a subcommand 'help' is found in the exec path, run it. Otherwise fall
    back to a simple usage message. Does not terminate execution.

    """
    help_executable = os.path.join(exec_path, 'help')
    if os.access(help_executable, os.R_OK|os.X_OK):
        subprocess.call([help_executable])
    else:
        logger.error("usage: %(SC_COMMAND)s COMMAND [ARGS...]\n" % os.environ)


def get_subcommand(args, exec_path):
    """Find the deepest executable file or directory that matches the command sequence.

    """
    for commands, commandargs in ((args[:i], args[i:]) for i in range(len(args), -1, -1)):
        subcommand = os.path.join(exec_path, *commands)
        if os.access(subcommand, os.R_OK|os.X_OK):
            break

    os.environ['SC_COMMAND'] = ' '.join((os.environ['SC_ARGV0'],) + commands)
    return subcommand, commandargs


def subcommander(argv0, *args):
    """

    "Options" are arguments that begin with '-'.

    The following options are special to subcommander-based tools, and will be
    plucked out of the command line for processing no matter where they appear:

    -h, --help
    -V, --version
    -v, --verbose

    All other options must appear AFTER the command sequence. Example:

    mytool foo --arg bar baz    # executes "foo" with arguments "--arg bar baz"
    mytool foo bar --arg baz    # executes "foo/bar" with arguments "--arg baz"
    mytool foo bar baz --arg    # executes "foo/bar/baz" with arguments "--arg"

    """
    argv0_basename = os.path.basename(argv0)
    os.environ['SC_ARGV0'] = argv0_basename
    rcfile = "%(HOME)s/.%(SC_ARGV0)src" % os.environ
    exec_path_envname = ('%s_EXEC_PATH' % argv0_basename).upper().replace(' ', '_')

    # Users shouldn't invoke 'subcommander' directly.
    if os.environ['SC_ARGV0'].startswith('subcommander'):
        # FIXME: this should instead walk a user through setting up a
        # subcommander-based tool, creating symlinks etc.
        raise CalledDirectlyError

    # create boilerplate rcfile if nonexistent
    if not os.path.exists(rcfile):
        create_rc_file(rcfile, exec_path_envname)

    # ensure rcfile is executable
    if not os.access(rcfile, os.X_OK):
        raise ConfigFileNotExecutableError(rcfile)

    # if we haven't set the "seen the rc file" flag, set it and bounce through
    # the rcfile
    if not os.environ.get('SC_RC_APPLIED'):
        os.environ['SC_RC_APPLIED'] = '1'
        return os.execv(rcfile, (rcfile, argv0) + args)

    exec_path = get_exec_path(exec_path_envname, rcfile)

    subcommand, args = get_subcommand(args, exec_path)

    if os.path.isdir(subcommand):
        show_help(subcommand)
        if args:
            raise UnknownSubcommandError(args)
        else:
            raise NoCommandSpecifiedError()

    # backwards compatibility with subcommander 0.x
    os.environ['SC_MAIN'] = os.environ['SC_ARGV0']
    os.environ['SC_NAME'] = os.environ['SC_COMMAND']

    # execv never returns; I 'return' to indicate execution won't continue
    return os.execv(subcommand, (subcommand,) + args)


def main():
    import sys
    logger.addHandler(logging.StreamHandler())
    try:
        return subcommander(*sys.argv)
    except SubcommanderUserError, e:
        # If a SubcommanderUserError occurs, show a normal-looking error
        # message, not a Python traceback.
        logger.error(e)
        return e.errno


if __name__ == '__main__':
    raise SystemExit(main())
