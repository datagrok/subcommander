#!/usr/bin/python

'''subcommander.py

A python implementation of subcommander.sh. It should work almost exactly the
same way.

'''

import os
import warnings


def format_msg(s):
    return ' '.join(l.strip() for l in s.strip().splitlines())


class CalledDirectlyError(EnvironmentError):
    def __init__(self):
        super(CalledDirectlyError, self).__init__(
            1,
            format_msg("""
                Subcommander is an abstraction that is not meant to be run
                under its own name. Instead, create a symlink to it, with a
                different name. And read the instructions."""))


class SubcommandDirectoryMissingError(EnvironmentError):
    def __init__(self, exec_path, scmd_name):
        super(SubcommandDirectoryMissingError, self).__init__(
            2,
            format_msg("""
                Subcommands directory does not exist. Place executable files
                there to enable them as sub-commands of '%s'""" % (
                    scmd_name)),
            exec_path)


class SpecifiedContextNotFoundError(EnvironmentError):
    def __init__(self, ctx_envname, environment_contextfile):
        super(SubcommandDirectoryMissingError, self).__init__(
            3,
            format_msg("""The context specified by %s does not exist""" % (
                scmd_name)),
            environment_contextfile)


def discover_context(context_filename):
    cwd = os.path.realpath(os.getcwd()).split(os.path.sep)
    for n in range(len(cwd), 0, -1):
        context_file = os.path.sep.join(cwd[0:n] + [context_filename])
        if os.path.exists(context_file):
            return context_file


def main(argv0, *args):
    argv0_basename = os.path.basename(argv0)
    rcfile = None

    is_subinvocation = bool(os.environ.get('SC_SUBLEVEL'))

    if is_subinvocation:
        name = '%s %s' % (os.environ['SC_NAME'], argv0_basename)
    else:
        tool_name = argv0
        scmd_name = argv0
        rcfile = "%(HOME)s/.%(SC_MAIN)src" % os.environ

    if tool_name.startswith('subcommander'):
        raise CalledDirectlyError

    if not os.environ.get('SC_IGNORE_RCFILE'):
        os.environ['SC_IGNORE_RCFILE'] = '1'
        if os.access(s, os.R_OK|os.X_OK):
            os.execv(rcfile, [argv0] + args)
        elif os.access(s, os.R_OK):
            warnings.warn("%s is not executable, and will be ignored." % rcfile)

    ctx_envname = '%s_CONTEXT' % tool_name.upper().replace(' ', '_')
    exec_path_envname = '%s_EXEC_PATH' % scmd_name.upper().replace(' ', '_')
    exec_path = os.environ.get(exec_path_envname, '%s.d' % argv0)

    if not os.path.isdir(exec_path):
        raise SubcommandDirectoryMissingError()

    environment_context = os.environ.get(ctx_envname)

    if not args:
        return "No COMMAND specified."

    subcommandbase = args.pop(0)
    subcommand = os.path.join(exec_path, subcommandbase)

    if not os.access(subcommand, os.R_OK|os.X_OK)
        return "Unknown %s command: %s" % (scmd_name, subcommandbase)

    context_filename = ".%s.context" % tool_name

    if not is_subinvocation:
        discovered_contextfile = discover_context(context_filename)

        if environment_context:
            environment_contextfile = os.path.join([environment_context, context_filename])
            if not os.path.exists(environment_contextfile):
                raise SpecifiedContextNotFoundError(ctx_envname, environment_contextfile)

        if (environment_context and discovered_contextfile
                and not os.path.samefile(
                    environment_context, discovered_contextfile)):
            warnings.warn(format_msg("""
                Context specified by %s=%s differs from and overrides context
                discovered at %s. Be sure that this is what you intend.""" % (
                    ctx_envname, environment_context, discovered_context)))

        if environment_contextfile:
            contextfile = environment_contextfile
        elif discovered_contextfile:
            contextfile = discovered_contextfile

        if os.access(subcommand, os.R_OK|os.X_OK):
            context = os.path.dirname(contextfile)
        elif os.access(subcommand, os.R_OK):
            raise EnvironmentError(4, "Context file must be executable", contextfile)
        else:
            context = None
            contextfile = None

    if os.path.samefile(argv0, subcommand):
        os.environ['SC_SUBLEVEL'] = 1
    else:
        try:
            del os.environ['SC_SUBLEVEL']
        except KeyError:
            pass

    os.environ['SC_MAIN'] = tool_name
    os.environ['SC_NAME'] = scmd_name
    os.environ['SC_CONTEXT'] = context

    os.execv([contextfile, subcommand] + args)


if __name__ == '__main__':
    import sys
    raise SystemExit(main(*sys.argv))
