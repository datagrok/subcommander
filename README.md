# Subcommander

Do you have a collection of tools and scripts that you've written to save time
at the command line? Is it hard to keep them documented, and difficult for new
teammates to get familiar with them? Subcommander is here to help.

Several familiar tools (like git, subversion, cvs, zip, even django-admin.py,
etc., follow a pattern where the main executable is invoked with an argument
naming another executable specific to that system. For example, `git push`
causes `git` to invoke `git-push`. This establishes a kind of "namespace" for
executables. Subcommander provides a kind of framework for quickly building
such executable namespaces.

Git also performs *context discovery* for its subcommands. Whenever git is
invoked, the first thing it does is identify what git repository you intend for
it to work with, by checking environment variables and walking up the directory
tree. Subcommander apes this as well, allowing your disparate tools to have an
easy way to determine the location of the root directory of the current
context/project/checkout/virtualenv you are working with.

Subcommander attempts to provide a simple way to encapsulate these patterns, so
you can get your piles of disparate scripts organized. It intends to be
**language agnostic**: all sub-commands and context files may be implemented in
any language. Subcommander itself happens to be implemented in shell script,
but this should make no difference to the user. The author plans to
re-implement in both Python and C.

## Setup

1. Clone this repository somewhere on your system.

2. If you don't have a ~/bin directory already, create it and add it to your
   path in your .profile:

3. Create a symlink to (or a copy of) the subcommander.sh script in ~/bin named
   for your tool.

4. Create a directory right next to it named that plus .d. This will hold the
   sub-scripts. You should now have:

		bin/
			mytool -> /path/to/lib/subcommander.sh
			mytool.d/

4. 'init' and 'help' are two subcommands included with subcommander that you
will probably want as well. Symlink to those from your scripts directory.

		bin/
			mytool -> /path/to/lib/subcommander.sh
			mytool.d/
				init -> /path/to/lib/subcommander/init
				help -> /path/to/lib/subcommander/help

5. Now you're ready to use your tool. It knows what directories it "owns" when
   you 'init' them, by creating a file named for itself plus ".context". Given
   this directory structure:

		foo/bar/
			baz1/
			baz2/
				quux/

From foo/bar, 'mytool init' produces:

		foo/bar/
			baz1/
			baz2/
				quux/
			.mytool.context

Then, from anywhere within foo/bar:

		mytool status

will source foo/bar/.mytool.context, and then execute ~/bin/mytool.d/status
with the following variables set:

		SC_CONTEXT  # The path to the context, in this case foo/bar
		SC_MAIN		# The basename of your tool

To see what variables are set by subcommander when it executes your tool, try
the `info` subcommand included with subcommander.

		ln -s /path/to/subcommander ~/bin/mytool/
		cd foo/bar
		mytool info

## Other tools like this one

There are many tools that accomplish something similar. This is my defense
against accusations of [NIH Syndrome][]. Here is a comparison of similar tools I
have found, and the reason why I created this instead of using them.

* [Wayne E. Seguin's BDSM](https://bdsm.beginrescueend.com/): Too complex, no context discovery(?), nsfw docs make my eyes bleed.
* [anandology/subcommand](https://github.com/anandology/subcommand): Requires commands to be implemented in Python.
* [jds/clik](https://github.com/jds/clik): Requires commands to be implemented in Python.
* [rkumar/subcommand](https://github.com/rkumar/subcommand): Requires commands to be implemented in Ruby.
* [reinh/commandant](https://github.com/reinh/commandant): Requires commands to be implemented in Ruby.
* [ander/subcommand](https://github.com/ander/subcommand): Requires commands to be implemented in Ruby.
* [tsantos/subcommander](https://github.com/tsantos/subcommander): Requires commands to be implemented in Ruby.
* [msassak/kerplutz](https://github.com/msassak/kerplutz): I can't really figure it out but I think it's Ruby-only.

[NIH Syndrome]: http://en.wikipedia.org/wiki/Not_Invented_Here
