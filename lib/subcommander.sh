#!/bin/sh
# Description: Runs subcommands
set -e

# subcommander
#
# First walk up the directory tree looking for a .$0.context file to source.
# Then it look for an executable named $0.d/$1 or $0.d/$1.* to execute.

# SC_MAIN holds the basename of the tool implemented by subcommander. For
# example, if 'cmc' is a symlink to subcommander.sh, SC_MAIN=cmc. If this is a
# multi-level invocation of subcommander, we use the original's rc files etc.
# and set SC_NAME to a space-separated list of all the sub-invocations. So:
# SC_MAIN = the main tool, like 'git'
# SC_NAME = the sub-sub commands as a list, like 'git stash pop'

# SC_SUBLEVEL is a flag we use to differentiate between subcommander calling
# itself as part of a heiarchy and subcommander calling some other
# subcommander-implemented tool from one of its subcommands. It is only set if
# this script detects that the one it is about to call is a symlink to the same
# place it itself is. FIXME TODO is this sufficient? Will break if one copies
# rather than links to subcommander.

if [ "$SC_SUBLEVEL" ]; then
	SC_NAME="$SC_NAME ${0##*/}"
	# If we're a sub-invocation, inherit SC_MAIN, append ourselves to SC_NAME,
	# don't do context discovery, don't bounce through the rcfile or the
	# contextfile.
	sc_rcfile=
	sc_contextfile=
else
	SC_MAIN="${0##*/}"
	SC_NAME="$SC_MAIN"
	sc_rcfile="$HOME/.$SC_MAIN.rc"
fi

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

if [ "$SC_MAIN" = "subcommander" -o "$SC_MAIN" = "subcommander.sh" ]; then
	abort <<- EOF
		Error: Subcommander is an abstraction that is not meant to be run under
		its own name. Instead, create a symlink to it, with a different name.
		And read the instructions.
	EOF
fi

# Environment variables that may be used to configure each tool implemented by
# subcommander. For example, if you have a tool named 'cmc' that is a symlink
# to subcommander, it will obey the environment variables CMC_CONTEXT and
# CMC_EXEC_PATH. Multi-level tools use the main tool's context but will accept
# their own exec_path. For example a sub-subcommander under 'cmc' called 'db'
# would examine CMC_DB_EXEC_PATH
ctx_envname="`echo $SC_MAIN|tr 'a-z ' 'A-Z_'`_CONTEXT"
eval "exec_path=\${`echo $SC_NAME|tr 'a-z ' 'A-Z_'`_EXEC_PATH:='$0.d'}"

if [ ! -d "$exec_path" ]; then
	abort <<-END
		Subcommands directory $exec_path does not exist. Place executable
		files there to enable them as sub-commands of '$SC_NAME'.
	END
fi

usage_abort () {
	usage
	if [ -x "$exec_path/help" ]; then
		export SC_MAIN SC_NAME
		echo
		"$exec_path/help"
	fi
	echo
	abort $1
}

usage () { cat <<-END
		usage: $SC_NAME COMMAND [OPTION...] [ARG]...
		
		OPTION may be one of:
		    -f Abort if the current context does not match \$$ctx_envname
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
#	${var%/*} is like `dirname $var`
#   ${var%.*} removes one level of filename extension
#   ${var%%.*} removes all filename extensions **
#	** This will fail if you don't ensure there are no '.' in the path!

context_mismatch_action='warn'
verbose=
eval "environment_context=\$$ctx_envname"

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

# Were we called with any arguments at all?
[ $# -gt 0 ] || usage_abort 2 <<-END
	No COMMAND specified.
END

subcommandbase="$1"
subcommand="$exec_path/$1"
shift

# Check to ensure subcommand is an executable
# TODO: Maybe if $subcommand not found, check also for executables named
# $subcommand.py, $subcommand.sh, etc.
[ -x "$subcommand" ] || abort <<-END
	error: unknown $SC_NAME command: $subcommandbase.
END

context_filename=".$SC_MAIN.context"

# If this is a multi-level invocation, don't do any context discovery or
# examination, just inherit it.
if [ ! "$SC_SUBLEVEL" ]; then
	# Find the nearest context file in the directory hierarchy.
	[ "$skip_context_discovery" ] || {
		# it's ok if this fails.
		cwd="$(pwd)"
		discovered_context=
		discovered_contextfile=
		while true; do
			if [ -e "$cwd/$context_filename" ]; then
				discovered_context="${cwd:-/}"
				discovered_contextfile="$cwd/$context_filename"
				break
			fi
			[ "$cwd" ] || break # if this was root, stop.
			cwd="${cwd%/*}" # go up one directory.
		done
	}

	# If context is manually set, ensure it exists.
	if [ "$environment_context" ]; then
		environment_contextfile="$environment_context/$context_filename"

		[ -f "$environment_contextfile" ] || abort 3 <<-END
			The context specified by $ctx_envname does not exist:
			$environment_contextfile not found.
		END
	fi

	# If both are set, see if one differs from the other. (Possibly confused user.)
	if [ "$environment_contextfile" -a "$discovered_contextfile" ]; then
		if [ ! "$environment_contextfile" -ef "$discovered_contextfile" ]; then
			warn <<-END
				Warning: Context specified by $ctx_envname=$environment_context
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

	# If this is a sublevel, we don't want to bounce through the rcfile or the
	# context file. We want to adopt the context found (or not) by the parent
	# subcommander.

	if [ -x "$contextfile" ]; then
		SC_CONTEXT=${contextfile%/*}
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
fi

# Is the subcommand we're about to execute also a subcommand? If so, tell it
# that it should not do context discovery. If not, unset that flag (in case it
# is already set in our environment)
if [ "$0" -ef "$subcommand" ]; then
	export SC_SUBLEVEL=1
else
	unset SC_SUBLEVEL
fi

# This is redundant, but serves to be a very explicit reminder of what
# variables are available in the environment.
export SC_MAIN SC_NAME SC_CONTEXT SC_SUBLEVEL
exec $sc_rcfile $contextfile "$subcommand" "$@"
