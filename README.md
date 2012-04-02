# Subcommander

Do you have a collection of tools and scripts that you've written to save time
at the command line? Is it hard to keep them documented, and difficult for new
teammates to get familiar with them?  Subcommander is here to help.

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

## Install

Clone this repository somewhere on your system.

## Example Configuration

Let's pretend that you have a collection of scripts in your `~/bin` directory that you use while working on your project: `proj_runserver`, `proj_db_start`, `proj_db_stop`, and `proj_deploy`. Let's use subcommander to clean this up a bit, and create a single tool named `proj`.

1. Create a symlink to (or a copy of) the subcommander.sh script in ~/bin named
   `proj`.

   		$ ln -s /path/to/lib/subcommander.sh ~/bin/proj

2. At this point, running `proj` will already produce useful information:

		$ proj
		Subcommands directory ~/bin/proj.d does not exist. Place executable
		files there to enable them as sub-commands of 'proj'.

3. Create a directory right next to `proj` named `proj.d`. This will hold all the
   sub-scripts.

   		$ mkdir ~/bin/proj.d

4. You should now have:

		bin/
			proj -> /path/to/lib/subcommander.sh
			proj.d/

5. `help` is a subcommand included with subcommander that you will probably want as well. Symlink to it from your scripts directory.

		$ ln -s /path/to/lib/subcommander/help ~/bin/proj.d/

4. You should now have:

		bin/
			proj -> /path/to/lib/subcommander.sh
			proj.d/
				help -> /path/to/lib/subcommander/help

4. Now, running `proj` produces:

		$ proj
		usage: proj COMMAND [OPTION...] [ARG]...

		Available proj commands are:
		   help                 Lists the available sub-commands (this text)

		No COMMAND specified.

Pretty good for two symlinks and a directory, eh?

5. Let's move your scripts into that scripts directory. Since we have a nice namespace, we can make their names a bit less verbose.

		$ mv ~/bin/proj_runserver ~/bin/proj.d/runserver
		$ mv ~/bin/proj_db_start ~/bin/proj.d/db_stop
		$ mv ~/bin/proj_db_stop ~/bin/proj.d/db_stop
		$ mv ~/bin/proj_deploy ~/bin/proj.d/deploy
		$ proj
		usage: proj COMMAND [OPTION...] [ARG]...

		Available proj commands are:
		   db_start
		   db_stop
		   deploy
		   help                 Lists the available sub-commands (this text)
		   runserver

		No COMMAND specified.

		$ proj db_start
		Starting the database...

## Improvements for subcommander-based sub-scripts

### Automatic descriptive text

Subcommander's `help` script has some built-in logic for pulling short descriptive text out of your scripts for display in the list of available commands. It's super simple: just add a comment near the top of your script that begins with "Desc" or "description" followed by a colon or equals, and a short line of text. Continuing with the examples above, let's add comments like these to our scripts:

		# Description: runs my server on port 8080

		/* Description: starts the database
		*/

		// desc: stops the database

		DESC=copies working directory up to server

The result:

		$ proj help
		Available proj commands are:
		   db_start             starts the database
		   db_stop              stops the database
		   deploy               copies working directory up to server
		   help                 Lists the available sub-commands (this text)
		   runserver            runs my server on port 8080

### Developing and debugging with `info`

To see what variables are set by subcommander when it executes your tool, try
the `info` subcommand included with subcommander.

		$ ln -s /path/to/lib/subcommander/info ~/bin/proj.d/
		$ proj info

### "I don't like `proj.d`"

A subcommander-based tool named `proj` will default to looking in the directory
`proj.d` in the same directory as `proj` for its subcommands. This may be
overridden by setting `PROJ_EXEC_PATH` in the environment.

You don't need to edit your startup scripts to set this into the environment.
Just add it to `~/.projrc`. See "Hook Scripts and Environment Variables" below
for details.

### Automatic context discovery

Subcommander-based tools know what directories they "own", and the `init` script is included to make the setup of a context easy.

		$ ln -s /path/to/lib/subcommander/init ~/bin/proj.d/

Now, let's say you're working on a version of your project, with a directory structure like this:

		devel/branch1/
			module1/
			module2/
				feature/

Within devel/branch1, `proj init` produces:

		devel/branch1/
			module1/
			module2/
				feature/
			.proj.context

Then, from anywhere within devel/branch1, running any `proj` command would
invoke it as before, but with the `SC_CONTEXT` environment variable set to `devel/branch1`.

### Integration with virtualenv

I dislike the way virtualenv's `bin/activate` works; I prefer a system level tool that launches a subshell.  Such a method is described here: [Virtualenv's bin/activate is Doing It Wrong](https://gist.github.com/2199506). You can enable it for use with a subcommand script like this:

		#!/bin/sh
		export VIRTUAL_ENV="$SC_CONTEXT"
		export PATH="$SC_CONTEXT/bin:$PATH"
		unset PYTHON_HOME
		exec "${@-:$SHELL}"

If you have already done `proj init` in the root of your virtualenv environment:

- `proj inve python` will run python as if it were being run after sourcing `bin/activate`.
- To simulate `bin/activate` try `proj inve`. Where you would normally use `deactivate`, just type CTRL+D or `exit`.
- Now `pip` behaves as you would expect. `pip` installs to your system or user-level environment unless you call it like `proj inve pip`.

### Hook scripts and environment variables

If you would like to call hook scripts or set variables into the environment
specific to your project, just add those commands to the context file
`.proj.context`. If you would like to hook into each invocation of your
script regardless of context, you may also create an executable script named
`~/.projrc`.

The context file is, by default, acutally an _executable shell script_. You can
replace it with any executable, written in any language, as long as you follow
its convention of executing (with `exec()`) its argument list.

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

## To Do:

- I built a much more robust and featureful `inve` at work, that checks that you are within a virtualenv environment, provides docs and friendly error messages, etc. Get permission to release it here, or re-write.
- Explore building unit tests for subcommander and subcommander-based tools using `chroot`. I would love some way to automatically verify whether or not all code paths in all of these scripts work perfectly on various unices-- Ubuntu, Debian, OS X, Arch, Red Hat.

## License

[AGPLv3](http://www.gnu.org/licenses/agpl.html). If you need something more corporate-friendly, contact me and I'll consider it.
