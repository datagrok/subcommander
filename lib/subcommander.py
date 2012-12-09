#!/usr/bin/python

'''subcommander.py

A python implementation of subcommander.sh. It should work almost exactly the
same way.

'''

import os
import warnings
import subprocess


def format_msg(s):
    """Helper that unindents and unwraps multiline docstrings."""
    return ' '.join(l.strip() for l in s.strip().splitlines())

def format_script(s):
    """Helper that unindents multiline docstrings."""
    return '\n'.join(l.strip() for l in s.strip().splitlines()) + '\n'


class SubcommanderUserError(Exception):
    """Subclasses of this class will not display a python traceback when thrown
    to the user.

    """
    pass


class CalledDirectlyError(EnvironmentError, SubcommanderUserError):
    def __init__(self):
        super(CalledDirectlyError, self).__init__(
            1,
            format_msg("""
                Subcommander is an abstraction that is not meant to be run
                under its own name. Instead, create a symlink to it, with a
                different name. And read the instructions."""))


class SubcommandDirectoryNotConfiguredError(EnvironmentError, SubcommanderUserError):
    def __init__(self, exec_path_envname, rcfile):
        super(SubcommandDirectoryNotConfiguredError, self).__init__(
            6,
            format_msg("""
                Could not find %s set in the environment. This should specify
                the path to subcommands. Recommend adding it to %s.""" % (
                    exec_path_envname, rcfile)))


class SubcommandDirectoryMissingError(EnvironmentError, SubcommanderUserError):
    def __init__(self, exec_path):
        super(SubcommandDirectoryMissingError, self).__init__(
            4,
            format_msg("""
                Subcommands directory does not exist. Place executable files
                there to enable them as sub-commands"""),
            exec_path)


class SpecifiedContextNotFoundError(EnvironmentError, SubcommanderUserError):
    def __init__(self, ctx_envname, environment_contextfile):
        super(SpecifiedContextNotFoundError, self).__init__(
            3,
            "The context specified by %s does not exist" % ctx_envname,
            environment_contextfile)


class NoCommandSpecifiedError(EnvironmentError, SubcommanderUserError):
    def __init__(self):
        super(NoCommandSpecifiedError, self).__init__(
            2,
            "No COMMAND specified.")


class ConfigFileNotExecutableError(EnvironmentError, SubcommanderUserError):
    def __init__(self, configfile):
        super(ConfigFileNotExecutableError, self).__init__(
            5,
            "Configuration file is not executable",
            configfile)


def discover_context(context_filename):
    cwd = os.path.realpath(os.getcwd()).split(os.path.sep)
    for n in range(len(cwd), 0, -1):
        context_file = os.path.sep.join(cwd[0:n] + [context_filename])
        if os.path.exists(context_file):
            return context_file


def create_rc_file(rcfile, exec_path_envname):
    """The rcfile does not exist, so create one prepopulated with some helpful
    comments.

    """
    print >> sys.stderr, "Creating rcfile %s." % rcfile
    with open(rcfile, 'w') as fp:
        fp.write(format_script("""
            #!/bin/sh

            # This file is executed by '%(SC_MAIN)s' every time you run a
            # '%(SC_MAIN)s' subcommand. You can edit this script, or replace it
            # with your own executable script or compiled program, so long as
            # you take care to exec() the command passed in as arguments, as is
            # done below.

            # This line sets %(execpathvar)s to ~/usr/lib/%(SC_MAIN)s unless it
            # is overridden in the environment.
            export %(exec_path_envname)s="${%(exec_path_envname)s:-~/usr/lib/%(SC_MAIN)s}"

            # If you have hooks to execute or customizations to make to the
            # environment, you may do so here.

            # The following line must be present for '%(SC_MAIN)s' to function.
            # It ends the script; any lines after it will never be reached.
            exec "$@"
            """ % {
                'exec_path_envname': exec_path_envname,
                'SC_MAIN': os.environ['SC_MAIN'],
            }))
        os.fchmod(fp.fileno(), 0755)


def main(argv0, *args):
    argv0_basename = os.path.basename(argv0)
    os.environ['SC_MAIN'] = argv0_basename
    os.environ['SC_NAME'] = argv0_basename
    rcfile = "%(HOME)s/.%(SC_MAIN)src" % os.environ
    ctx_envname = ('%s_CONTEXT' % argv0_basename).upper().replace(' ', '_')
    exec_path_envname = ('%s_EXEC_PATH' % argv0_basename).upper().replace(' ', '_')

    # Users shouldn't invoke 'subcommander' directly.
    if os.environ['SC_MAIN'].startswith('subcommander'):
        raise CalledDirectlyError

    # re-exec ourselves after bouncing through rcfile.
    if args and args[0] == '--subcommander-skip-rcfile':
        args = args[1:]
    else:
        if not os.path.exists(rcfile):
            create_rc_file(rcfile)
        if not os.access(rcfile, os.X_OK):
            raise ConfigFileNotExecutableError(rcfile)
        # I say "return" but technically execv aborts here.
        return os.execv(rcfile, (rcfile, argv0, '--subcommander-skip-rcfile') + args)

    try:
        exec_path = os.environ[exec_path_envname]
    except KeyError:
        raise SubcommandDirectoryNotConfiguredError(exec_path_envname, rcfile)

    exec_path = os.path.expanduser(exec_path)

    if not os.path.isdir(exec_path):
        raise SubcommandDirectoryMissingError(exec_path)

    environment_context = os.environ.get(ctx_envname)

    if not args:
        help_executable = '%s/help' % exec_path
        if os.access(help_executable, os.R_OK|os.X_OK):
            subprocess.call([help_executable])
        else:
            print >> sys.stderr, "usage: %(SC_NAME)s COMMAND [ARGS...]\n" % os.environ
        raise NoCommandSpecifiedError()

    subcommandbase = args.pop(0)
    subcommand = os.path.join(exec_path, subcommandbase)

    if not os.access(subcommand, os.R_OK|os.X_OK):
        return "Unknown %s command: %s" % (os.environ['SC_NAME'], subcommandbase)

    context_filename = ".%(SC_MAIN)s.context" % os.environ

    discovered_contextfile = discover_context(context_filename)

    if environment_context:
        environment_contextfile = os.path.join([
            environment_context, context_filename])
        if not os.path.exists(environment_contextfile):
            raise SpecifiedContextNotFoundError(
                    ctx_envname, environment_contextfile)

    if (environment_context and discovered_contextfile
            and not os.path.samefile(
                environment_context, discovered_contextfile)):
        warnings.warn(format_msg("""
            Context specified by %s=%s differs from and overrides context
            discovered at %s. Be sure that this is what you intend.""" % (
                ctx_envname, environment_context, discovered_contextfile)))

    if environment_contextfile:
        contextfile = environment_contextfile
    elif discovered_contextfile:
        contextfile = discovered_contextfile

    if os.access(subcommand, os.R_OK|os.X_OK):
        os.environ['SC_CONTEXT'] = os.path.dirname(contextfile)
    elif os.access(subcommand, os.R_OK):
        raise EnvironmentError(4, "Context file must be executable", contextfile)
    else:
        del os.environ['SC_CONTEXT']
        contextfile = None

    if contextfile:
        os.execv(contextfile, (contextfile, subcommand) + args)
    else:
        os.execv(subcommand, (subcommand,) + args)


if __name__ == '__main__':
    import sys
    try:
        raise SystemExit(main(*sys.argv))
    except SubcommanderUserError, e:
        print >> sys.stderr, e
        raise SystemExit(e.errno)
