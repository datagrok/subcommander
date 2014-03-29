# Subcommander

Note: You are on the 'v0.x' branch of subcommander. I have a python-based
rewrite in development; see branch 'x1.x'.

---

Do you have a collection of tools and scripts that you've written to save time
at the command line? Is it hard to keep them documented, and difficult for new
teammates to get familiar with them?  Subcommander is here to help.

Several familiar tools (like git, subversion, cvs, zip, even django-admin.py,
etc., follow a pattern where the main executable is invoked with an argument
naming another executable specific to that system. For example, `git push`
causes `git` to invoke `git-push`. This establishes a kind of "namespace" for
executables.

Git also performs *context discovery* for its subcommands. Whenever git is
invoked, the first thing it does is identify what git repository you intend for
it to work with, by checking environment variables and walking up the directory
tree. Subcommander apes this as well, allowing your disparate tools to have an
easy way to determine the location of the root directory of the current
context/project/checkout/virtualenv you are working with.

Subcommander attempts to provide a simple way to encapsulate these patterns, so
you can get your piles of disparate scripts organized. It intends to be
**language agnostic**: all sub-commands and context files may be implemented in
any number of languages. Subcommander itself happens to be implemented in shell
script, but this should make no difference to the user. The author plans to
re-implement in both Python and C.

## Install

Clone this repository somewhere on your system.

## Example Configuration

Let's pretend that you have a collection of scripts in your `~/bin` directory
that you use while working on your project: `proj_runserver`, `proj_db_start`,
`proj_db_stop`, and `proj_deploy`. Let's use subcommander to clean this up a
bit, and create a single tool named `proj`.

1. Create a symlink to (or a copy of) the subcommander.sh script in ~/bin named
   `proj`.

        $ ln -s /path/to/lib/subcommander.sh ~/bin/proj

2. At this point, running `proj` will already produce useful information:

        $ proj
        Subcommands directory ~/bin/proj.d does not exist. Place executable
        files there to enable them as sub-commands of 'proj'.

3. So, do what it recommends. Create a directory right next to `proj` named
   `proj.d`. This will hold all the sub-scripts.

        $ mkdir ~/bin/proj.d

4. You should now have:

        bin/
        ├── proj -> /path/to/lib/subcommander.sh
        └── proj.d/

5. `help` is a subcommand included with subcommander that you will probably
   want as well. Symlink to it from your scripts directory.

        $ ln -s /path/to/lib/subcommander/help ~/bin/proj.d/

4. You should now have:

        bin/
        ├── proj -> /path/to/lib/subcommander.sh
        └── proj.d/
            └── help -> /path/to/lib/subcommander/help

4. Now, running `proj` produces:

        $ proj
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj commands are:
           help                 Lists the available sub-commands (this text)

        No COMMAND specified.

Pretty good for two symlinks and a directory, eh?

5. Let's move your scripts into that scripts directory. Since we have a nice
   namespace, we can make their names a bit less verbose.

        $ mv ~/bin/proj_db_start ~/bin/proj.d/db_start
        $ mv ~/bin/proj_db_stop ~/bin/proj.d/db_stop
        $ mv ~/bin/proj_deploy ~/bin/proj.d/deploy
        $ mv ~/bin/proj_runserver ~/bin/proj.d/runserver

        $ tree ~/bin
        ~/bin/
        ├── proj -> /path/to/lib/subcommander.sh
        └── proj.d/
            ├── db_start
            ├── db_stop
            ├── deploy
            ├── help -> /path/to/lib/subcommander/help
            └── runserver

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

Subcommander's `help` script has some built-in logic for pulling short
descriptive text out of your scripts for display in the list of available
commands. It's super simple: just add a comment near the top of your script
that begins with "Desc" or "description" followed by a colon or equals, and a
short line of text. Continuing with the examples above, let's add comments like
these to our scripts:

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

### Sub-sub-commands

In the example above, we have two commands `db_start` and `db_stop` that could
be further cleaned up. In the same way that we created the initial tool `proj`,
we can also create a `proj db` which itself launches subcommands:

        $ ln -s /path/to/lib/subcommander.sh ~/bin/proj.d/db
        $ mkdir ~/bin/proj.d/db.d
        $ mv ~/bin/proj.d/db_start ~/bin/proj.d/db.d/start
        $ mv ~/bin/proj.d/db_stop ~/bin/proj.d/db.d/stop

        $ tree ~/bin
        ~/bin/
        ├── proj -> /path/to/lib/subcommander.sh
        └── proj.d/
            ├── db -> /path/to/lib/subcommander.sh
            ├── db.d/
            │   ├── start
            │   └── stop
            ├── deploy
            ├── help -> /path/to/lib/subcommander/help
            └── runserver

        $ proj
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj commands are:
           db                   Runs subcommands
           deploy               copies working directory up to server
           help                 Lists the available sub-commands (this text)
           runserver            runs my server on port 8080

        No COMMAND specified.

        $ proj db
        usage: proj COMMAND [OPTION...] [ARG]...

        Available proj db commands are:
           start                starts the database
           stop                 stops the database

        No COMMAND specified.

        $ proj db_start
        Starting the database...

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

These names are dependent on what you name your tool. If instead of `proj` you
called your tool `foo`, you would want to put subcommands in `foo.d`, use
`FOO_EXEC_PATH` to override that location, and put `foo`-specific configuration
in `~/.foorc`.

### Automatic context discovery

Subcommander-based tools know what directories they "own", and the `init`
script is included to make the setup of a context easy.

        $ ln -s /path/to/lib/subcommander/init ~/bin/proj.d/

Now, let's say you're working on a version of your project, with a directory
structure like this:

        devel/branch1/
        ├── module1/
        └── module2/
            └── feature/

Within devel/branch1, `proj init` produces:

        devel/branch1/
        ├── module1/
        ├── module2/
        │   └── feature/
        └── .proj.context

Then, from anywhere within `devel/branch1`, running any `proj` command would
invoke it as before, but with the `SC_CONTEXT` environment variable set to
`devel/branch1`.

### Hook scripts and environment variables

If you would like to call hook scripts or set variables into the environment
every time you use `proj`, add them to `~/.projrc`.

If you want to call hook scripts or set variables specific to your project, add
those commands to the context file `.proj.context` in the root of your proj
context.

The context file `.proj.context` and rc file `~/.projrc` are by default
_executable shell scripts_. You can replace them with any executable, written
in any language, as long as you follow their convention of executing (with
`exec()`) their argument list. Here's a context file that sets one environment
variable:

    #!/bin/sh
    export FOO_PATH="/tmp/foo"
    exec "$@"

Here it is again, in Python:

    #!/usr/bin/python
    import os
    os.environ['FOO_PATH'] = '/tmp/foo'
    os.execv(*sys.argv[1:])

It doesn't even need to be a script. Here it is again, as a C program you can
compile and use as a context file. (Though I can't imagine why anybody would do
this.)

    #include <stdio.h>
    int main(int argc, char *argv[])
    {
        setenv("FOO_PATH", "/tmp/foo", 1);
        return execvp(argv[1], &(argv[1]));
    }

Now, whenever a subcommand is executed by `proj`, the environment variable
`FOO_PATH` will be set to `/tmp/foo`.

**Remember: Subcommander configuration files are just normal executables that
exec() their arguments.**

These names are dependent on what you name your tool. If instead of `proj` you
called your tool `foo`, your context files would be named `.foo.context`, and
your rc file would be named `~/.foorc`.

### Integration with virtualenv

I dislike the way virtualenv's `bin/activate` works; I prefer a system level
tool that launches a subshell. Such a method is described here: [Virtualenv's
bin/activate is Doing It Wrong](https://gist.github.com/2199506). You can
enable it for use with a subcommand script like this, which I call `inve`, for
"in the virtualenv":

        #!/bin/sh
        export VIRTUAL_ENV="$SC_CONTEXT"
        export PATH="$SC_CONTEXT/bin:$PATH"
        unset PYTHON_HOME
        exec "${@-:$SHELL}"

If you have already done `proj init` in the root of your virtualenv environment:

- `proj inve python` will run python as if it were being run after sourcing
  `bin/activate`.
- To simulate `bin/activate` try `proj inve`. Where you would normally use
  `deactivate`, just type CTRL+D or `exit`.
- Now `pip` behaves as you would expect. `pip` installs to your system or
  user-level environment unless you call it like `proj inve pip`.

## Other tools like this one

There are many tools that accomplish something similar. This is my defense
against accusations of [NIH Syndrome][]. Here is a comparison of similar tools
I have found, and the reason why I created this instead of using them.

* [37signals/sub](https://github.com/37signals/sub): This tool adopts many of the same principles as Subcommander, such as language-agnosticism. I discovered it months after I had written Subcommander. You might consider it if you prefer its license or architecture. There's a good introduction in this blog post: [Automating with convention: Introducing sub](http://37signals.com/svn/posts/3264-automating-with-convention-introducing-sub])

Others:

* [jwmayfield/fn](https://github.com/jwmayfield/fn) a "personalization of 37signals/sub"
* [Wayne E. Seguin's BDSM](https://bdsm.beginrescueend.com/): Too complex, no context discovery(?), nsfw docs make my eyes bleed. From the developer of [RVM](http://rvm.io/).
* [anandology/subcommand](https://github.com/anandology/subcommand): Requires commands to be implemented in Python.
* [jds/clik](https://github.com/jds/clik): Requires commands to be implemented in Python.
* [rkumar/subcommand](https://github.com/rkumar/subcommand): Requires commands to be implemented in Ruby.
* [reinh/commandant](https://github.com/reinh/commandant): Requires commands to be implemented in Ruby.
* [ander/subcommand](https://github.com/ander/subcommand): Requires commands to be implemented in Ruby.
* [tsantos/subcommander](https://github.com/tsantos/subcommander): Requires commands to be implemented in Ruby.
* [msassak/kerplutz](https://github.com/msassak/kerplutz): I can't really figure it out but I think it's Ruby-only.
* [fabric/fabric](https://github.com/fabric/fabric): Subcommands are implemented in Python. Strange command-line interface to support running commands on multiple remote hosts at once. Treats local host as remote host.
* [anandology/subcommand](https://github.com/anandology/subcommand): Requires subcommands to be implmented in Python.
* [GaretJax/subcommands](https://github.com/GaretJax/subcommands)
* [will0/instacmd](https://github.com/will0/instacmd)
* [repejota/subcmd](https://github.com/repejota/subcmd)
* [m1m0r1/argtools.py](https://github.com/m1m0r1/argtools.py)
* [dbrock/exec-longest-prefix](https://github.com/dbrock/exec-longest-prefix)
* [nicksloan/subcommander](https://github.com/nicksloan/subcommander)
* [optparse-subcommand](https://github.com/bjeanes/optparse-subcommand) Ruby.
* [ander/subcommand](https://github.com/ander/subcommand) Ruby.
* [domnikl/subcommand](https://github.com/domnikl/subcommand) Go.

It may be simple to create a small launcher for scripts in other languages, but
that means every time you add, move, or rename a script you'd have to touch
some main file. Subcommander is entirely configured by the existence of a
script at a particular place in the filesystem.

[NIH Syndrome]: http://en.wikipedia.org/wiki/Not_Invented_Here

## To Do:

- I built a much more robust and featureful `inve` at work, that checks that
  you are within a virtualenv environment, provides docs and friendly error
  messages, etc. Get permission to release it here, or re-write.
- Explore building unit tests for subcommander and subcommander-based tools
  using `chroot`. I would love some way to automatically verify whether or not
  all code paths in all of these scripts work perfectly on various unices--
  Ubuntu, Debian, OS X, Arch, Red Hat.
- Employ another way to get descriptive text; we won't be able to parse
  binaries for 'Description:' lines.

## License

[GPLv3](http://www.gnu.org/licenses/gpl.html)
