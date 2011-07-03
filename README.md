# Subcommander

Do you have a collection of tools and scripts that you've written that you use
in your organization? Is it hard to keep them documented, and for new teammates
to get familiar with them? Subcommander is here to help.

Several advanced tools (like git, subversion, cvs, zip, even django-admin.py,
etc., follow a pattern where the main tool is invoked with an argument naming a
subcommand specific to that system. This acts as a somewhat informal namespace
for executables.

Git also performs context discovery for its subcommands. Whenever git is
invoked, the first thing it does is identify what git repository you intend for
it to work with, by checking environment variables and walking up the directory
tree. Subcommander apes this as well, allowing your disparate tools to have an
easy way to determine the location of the root directory of the current
context/project/checkout/virtualenv you are working with.

Subcommander attempts to provide a simple way to encapsulate these patterns, so
you can get your piles of disparate scripts organized.

## Setup

1. Create a symlink to (or a copy of) the subcommander.sh script in ~/bin named
for your tool.

2. Create a directory right next to it named that plus .d, this will hold the
sub-scripts.

3. In ~/.profile: export PATH=~/bin:$PATH

		bin/
			mytool -> /path/to/lib/subcommander.sh
			mytool.d/

4. 'init' and 'help' are two subcommands included with subcommander that you
will probably want as well. Symlink to (or copy of) those from your scripts
directory.

		bin/
			mytool -> /path/to/lib/subcommander.sh
			mytool.d/
				init -> /path/to/lib/subcommander/init
				help -> /path/to/lib/subcommander/help

5. Now you're ready to use your tool. It knows what directories it "owns" when
you 'init' them, by creating a file named for itself plus ".context":

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

...wip...
