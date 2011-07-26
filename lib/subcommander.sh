#!/bin/sh
# Description: Runs subcommands
set -e

# subcommander
#
# First walk up the directory tree looking for a .$0.context file to source.
# Then it look for an executable named $0.d/$1 or $0.d/$1.* to execute.

# SUBCOMMANDER holds the basename of the tool implemented by subcommander. For
# example, if 'cmc' is a symlink to subcommander.sh, SUBCOMMANDER=cmc. If this
# is a multi-level invocation of subcommander, use the original's rc files etc.
if [ ! "$SUBCOMMANDER" ]; then
	SUBCOMMANDER="${0##*/}"
fi
sc_rcfile="$HOME/.$SUBCOMMANDER.rc"

# FIXME: My convention for $my_exec_path isn't very unix-y. Most tools, if
# installed in /usr/bin, would keep their executable sub-scripts in
# "/usr/lib/$0/". C.f. /usr/lib/xscreensaver/, /usr/lib/git-core/.

# FIXME: Subcommander isn't expected to be executed under its original name;
# perhaps it too should live in a 'lib' directory? Maybe TODO: detect if this
# script is being run as 'subcommander' and output a message explaining that's
# not expected and how to set up a new tool based on it.

# FIXME instead of symlinking to subcommander, could it be sourced instead? I
# think I prefer the symlink convention because that enables subcommander to be
# rewritten in any language.

# FIXME: This will be a lot more impressive if I can rig up an automatic
# bash-completion helper. TODO implement as a subcommand like 'help'.

# Environment variables that may be used to configure each tool implemented by
# subcommander. For example, if you have a tool named 'cmc' that is a symlink
# to subcommander, it will obey the environment variables CMC_CONTEXT and
# CMC_EXEC_PATH.
sc_env_prefix="`echo $SUBCOMMANDER|tr 'a-z ' 'A-Z_'`"
sc_ctx_envname="${sc_env_prefix}_CONTEXT"
eval "my_exec_path=\${${sc_env_prefix}_EXEC_PATH:='$0.d'}"

usage () { cat <<-END
		usage: $SUBCOMMANDER COMMAND [OPTION...] [ARG]...
		
		OPTION may be one of:
		    -f Abort if the current context does not match \$$sc_ctx_envname
		    -q Be quiet
		    -s Do not perform context discovery
		    -v Be more verbose
	END
}

# TODO: Integrate with prompt and/or window title? I wouldn't like that by
# default, perhaps provide a hook mechanism.
#
# TODO: Compare techniques and sanity checks with those in git.
# https://github.com/git/git/blob/master/git.c

# Bash reminders:
# 	${var##*/} is like `basename $var`
#	${var%/.*} is like `dirname $var`
#   ${var%.*} removes one level of filename extension
#   ${var%%.*} removes all filename extensions **
#	** This will fail if you don't ensure there are no '.' in the path!

context_mismatch_action='warn'
verbose=
eval "environment_context=\$$sc_ctx_envname"

while getopts sfqv f
do
	case "$f" in
		s)	skip_context_discovery=1
			;;
		f)	context_mismatch_action='abort'
			;;
		q)	context_mismatch_action='ignore'
			verbose=
			;;
		v)	verbose=1
	esac
done
shift $(($OPTIND - 1))


# Functions which take messages as standard input
warn () {
	fmt >&2
}
ignore () {
	cat > /dev/null
}
abort () {
	warn; exit $1
}
usage_abort () {
	usage
	if [ -x "$my_exec_path/help" ]; then
		echo
		"$my_exec_path/help"
	fi
	echo
	abort $1
}

# Were we called with any arguments at all?
[ $# -gt 0 ] || usage_abort 2 <<-END
	No COMMAND specified.
END

subcommandbase="$1"
subcommand="$my_exec_path/$1"
shift; subcommandargs="$@"

# Find the nearest context file in the directory hierarchy.
[ "$skip_context_discovery" ] || {
	# it's ok if this fails.
	discovered_contextfile=`acquire ".$SUBCOMMANDER.context"` || true
	discovered_context="${discovered_contextfile%/*}"
}

# If context is manually set, ensure it exists.
if [ "$environment_context" ]; then
	environment_contextfile="$environment_context/.$SUBCOMMANDER.context"

	[ -f "$environment_contextfile" ] || abort 3 <<-END
		The context specified by $sc_ctx_envname does not exist:
		$environment_contextfile not found.
	END
fi

# If both are set, see if one differs from the other. (Possibly confused user.)
if [ "$environment_contextfile" -a "$discovered_contextfile" ]; then
	if [ ! "$environment_contextfile" -ef "$discovered_contextfile" ]; then
		warn <<-END
			Warning: Context specified by $sc_ctx_envname=$environment_context
			differs from and overrides context discovered at $discovered_context.
			Be sure that this is what you intend.
		END
	fi
fi

# Prefer environment-specified context over discovered context.
# TODO: prefer argument-specified context over both.
if [ "$environment_contextfile" ]; then
	contextfile="$environment_contextfile"
elif [ "$discovered_contextfile" ]; then
	contextfile="$discovered_contextfile"
fi

# Check to ensure subcommand is an executable
# TODO: Maybe if $subcommand not found, check also for executables named
# $subcommand.py, $subcommand.sh, etc.
[ -x "$subcommand" ] || abort <<-END
	error: unknown $SUBCOMMANDER command: $subcommandbase.
END

# Launch subcommand.

if [ -x "$sc_rcfile" ]; then
	# If you would like to specify a user-level configuration file and/or hook
	# script, create it at $sc_rcfile and mark it executable.  It will be
	# exec()d with arguments specifying the name and arguments of the command
	# it should exec() in turn.
	true # noop
elif [ -e "$sc_rcfile" ]; then
	# TODO FIXME create a trampoline that will source non-executable key/value pairs
	echo "Warning: $sc_rcfile is not executable, and will be ignored" | warn
else
	# It is OK if $sc_rcfile does not exist.
	sc_rcfile=
fi

if [ -x "$contextfile" ]; then
	SC_CONTEXT=${contextfile%/.*}
	# Project-level configuration and/or hooks, are created by subcommander's
	# included 'init' subcommand. It will be exec()d with arguments specifying
	# the name and arguments of the command it should exec() in turn.

	# TODO FIXME create a trampoline that will source non-executable key/value pairs
elif [ -e "$contextfile" ]; then
	# TODO FIXME include a trampoline to handle non-executable files too.
	# This is currently an abort.
	echo "Context file $contextfile must be executable." | abort
else
	# If the context does not exist, that's tolerable, we are simply not within
	# a subcommander context. Subcommands should however be careful to act
	# appropriately in this case.
	[ "$verbose" ] && echo "Note: no context was found." | warn
	SC_CONTEXT=
	contextfile=
fi

export SUBCOMMANDER SC_CONTEXT
exec $sc_rcfile $contextfile "$subcommand" "$subcommandargs"
