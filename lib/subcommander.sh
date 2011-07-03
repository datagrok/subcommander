#!/bin/sh

# subcommander
#
# First walk up the directory tree looking for a .$0.context file to source.
# Then it look for an executable named $0.d/$1 or $0.d/$1.* to execute.

export SUBCOMMANDER="${0##*/}"
export SC_EXEC_PATH="$0.d"

# FIXME: My convention for $SC_EXEC_PATH isn't very unix-y. Most tools, if
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

SC_CTX_ENVNAME="`echo $SUBCOMMANDER|tr 'a-z ' 'A-Z_'`_CONTEXT"

usage () { cat <<-END
		usage: $SUBCOMMANDER COMMAND [OPTION...] [ARG]...
		
		OPTION may be one of:
		    -f Abort if the current context does not match \$$SC_CTX_ENVNAME
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
eval "environment_context=\$$SC_CTX_ENVNAME"

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
	if [ -x "$SC_EXEC_PATH/help" ]; then
		echo
		"$SC_EXEC_PATH/help"
	fi
	echo
	abort $1
}

# Were we called with any arguments at all?
[ $# -gt 0 ] || usage_abort 2 <<-END
	No COMMAND specified.
END

subcommandbase="$1"
subcommand="$SC_EXEC_PATH/$1"
shift; subcommandargs="$@"

# Find the nearest context file in the directory hierarchy.
[ "$skip_context_discovery" ] || {
	discovered_contextfile=`acquire ".$SUBCOMMANDER.context"`
	discovered_context="${discovered_contextfile%/*}"
}

# If context is manually set, ensure it exists.
if [ "$environment_context" ]; then
	environment_contextfile="$environment_context/.$SUBCOMMANDER.context"

	[ -f "$environment_contextfile" ] || abort 3 <<-END
		The context specified by $SC_CTX_ENVNAME does not exist:
		$environment_contextfile not found.
	END
fi

# If both are set, see if one differs from the other. (Possibly confused user.)
if [ "$environment_contextfile" -a "$discovered_contextfile" ]; then
	if [ ! "$environment_contextfile" -ef "$discovered_contextfile" ]; then
		warn <<-END
			Warning: Context specified by $SC_CTX_ENVNAME=$environment_context
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

# Source context or mention that it is non-existent.
if [ "$contextfile" ]; then
	[ "$verbose" ] && echo "Sourcing context $contextfile..." | warn
	set -a
	. "$contextfile"
	set +a
	context=${contextfile%/.*}
else
	[ "$verbose" ] && echo Note: no context was found. | warn
fi

# Check to ensure subcommand is an executable
# TODO: Maybe if $subcommand not found, check also for executables named
# $subcommand.py, $subcommand.sh, etc.
[ -x "$subcommand" ] || abort <<-END
	error: unknown $SUBCOMMANDER command: $subcommandbase.
END

# Launch subcommand.
export verbose
export SC_CTX_ENVNAME
eval "export $SC_CTX_ENVNAME='$context'"
exec "$subcommand" "$subcommandargs"
