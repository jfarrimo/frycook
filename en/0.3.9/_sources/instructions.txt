Intro
=====

Frycook is a system for installing and maintaining software on Linux
computers.  It consists of a framework to build systems with and a
program you run to apply the things you built with the framework to your
computers.

At the highest level Frycook depends on recipes and cookbooks to define
how systems are built.  Recipes and cookbooks in turn use settings,
environments, and packages to do their work.  The settings and
environments are passed around within the framework as json-translatable
dictionaries.  Packages live on disk as directories and files.

Settings and environments exist as json-like dictionaries because they
are easy to turn into json files, and then read back from them, and
because most templating engines expect dictionaries to be passed to them
in order to render their contents.  This means that these dictionaries
map nicely to both the storage and rendering functions and keep frycook
simple.

Recipes and cookbooks are python code that get executed when building
and updating servers.  Each recipe and cookbook lives in its own file.

Setup
=====

Before you can do anything with frycook, you'll need to install its
python package from pypi.  I usually create a virtualenv to run it in,
but it can also be installed globally::

    $ pip install frycook

Globules
========

All the user-generated files necessary for frycook to function are
usually arranged in a directory structure that I call a *globule*.  The
rest of these instructions will walk you through this globule and
explain all the pieces and how they work together.

Here's an example globule::

    sample                     # root directory
      packages                 # directory for the package files
        example_com            # root for example_com package files
          etc                  # corresponds to /etc on the target server
            nginx              # corresponds to /etc/nginx on the target server
              sites-available  # corresponds to /etc/nginx/sites-available on the target server
                example.com    # corresponds to /etc/nginx/sites-available/example.com on the target server
        hosts                  # root for hosts package files
          etc                  # corresponds to /etc on the target server
            hostname.tmplt     # template that becomes /etc/hostname on the target server
            hosts.tmplt        # template that becomes /etc/hosts on the target server
        nginx                  # root for nginx package files
          etc                  # corresponds to /etc directory on the target server
            default            # corresponds to /etc/default directory on the target server
              nginx            # corresponds to /etc/default/nginx file on the target server
            nginx              # corresponds to /etc/nginx directory on target server
              nginx.conf       # corresponds to /etc/nginx/nginx.conf file on target server
              sites-available  # corresponds to /etc/nginx/sites-available directory on target server
                default        # corresponds to /etc/nginx/sites-available/default directory on target server
                fck_delete.txt # lists files to delete from /etc/nginx/sites-available on target server
          srv                  # corresponds to /srv directory on the target server
            www                # corresponds to /srv/www directory on the target server
              50x.html         # corresponds to /srv/www/50x.html file on target server
              index.html       # corresponds to /srv/www/index.html file on target server
        postfix                # root for postfix package files
          etc                  # corresponds to /etc directory on the target server
            aliases            # corresponds to /etc/aliases directory on the target server
            mailname.tmplt     # template that becomes /etc/mailname on the target server
            postfix            # corresponds to /etc/postfix directory on the target server
              main.cf.tmplt    # template that becomes /etc/postfix/main.cf on the target server
        shorewall              # root for shorewall package files
          etc                  # corresponds to /etc directory on the target server
            default            # corresponds to /etc/default directory on the target server
              shorewall        # corresponds to /etc/default/shorewall directory on the target server
            shorewall          # corresponds to /etc/shorewall directory on the target server
              interfaces.tmplt # template that becomes /etc/shorewall/interfaces on the target server
        ssh                    # root for ssh package files
          etc                  # corresponds to /etc directory on the target server
            ssh                # corresponds to /etc/ssh directory on the target server
              sshd_config      # corresponds to /etc/ssh/sshd_config directory on the target server
      setup                    # directory for non-package files
        comp_dev.json          # included environment file for computer named dev
        environment.json       # environment file
        requirements.txt       # python pip requirements file
        runner.sh              # wrapper for frycooker.py that sets PYTHONPATH
        settings.json          # settings file
        cookbooks              # directory to hold the cookbooks package
          __init__.py          # define the cookbook list here and import all cookbook classes
          base.py              # cookbook referencing all the recipes for a base server setup
          web.py               # cookbook for make a base server into a web server
        recipes                # directory to hold the recipes package
          __init__.py          # define the recipe list here and import all recipe classes
          example_com.py       # recipe for setting up example.com on a web server
          fail2ban.py          # recipe for setting up fail2ban
          hosts.py             # recipe for setting up the /etc/hosts file
          nginx.py             # recipe for setting up nginx
          postfix.py           # recipe for setting up postfix
          root_user.py         # recipe for setting the root user's authorized_keys file
          shorewall.py         # recipe for setting up shorewall
          ssh.py               # recipe for setting up ssh

Recipes
=======

Recipes define subsystems that are distinct parts of larger systems.
They are the basic units of setup in frycook.  Generally a recipe
corresponds to an os-level package that needs to be installed or configured.

example recipe
--------------

This example sets up the hosts file on a computer::

    import cuisine

    from frycook import Recipe


    class RecipeHosts(Recipe):
        def apply(self, computer):
            group = self.environment["computers"][computer]["host_group"]
            computers = self.environment["groups"][group]["computers"]
            sibs = [comp for comp in computers if comp != computer]
            tmp_env = {"host": computer,
                       "sibs": sibs,
                       "computers": self.environment["computers"]}
            self.push_package_file_set('hosts', computer, tmp_env)

            cuisine.sudo("service hostname restart")

recipe list
-----------

There should be a recipe list in the ``__init__.py`` file for the packge.
This lists all the avilable recipes that cookbooks and frycooker.py can
reference.

Here's the sample ``__init__.py`` file::

    from fail2ban import RecipeFail2ban
    from hosts import RecipeHosts
    from nginx import RecipeNginx
    from postfix import RecipePostfix
    from root_user import RecipeRootUser
    from example_com import RecipeExampleCom
    from shorewall import RecipeShorewall
    from ssh import RecipeSSH

    recipes = {
        'fail2ban': RecipeFail2ban,
        'hosts': RecipeHosts,
        'nginx': RecipeNginx,
        'postfix': RecipePostfix,
        'root_user': RecipeRootUser,
        'example_com': RecipeExampleCom,
        'shorewall': RecipeShorewall,
        'ssh': RecipeSSH
        }

idempotence
-----------

One thing to keep in mind when creating recipes and cookbooks is
idempotency.  By keeping idempotency in mind in general you can create
recipes that you can run again and again to push out minor changes to a
package.  This way your recipes become the only way that you modify your
servers and can be a single chokepoint that you can monitor to make sure
things happen properly.

Lots of the cuisine functions you'll use have an "ensure" version that
first checks to see if a condition is true before applying it, such as
checking if a package is installed before trying to install it.  This is
nice when things could cause undesired configuration changes or
expensive operations that you don't want to happen every time.  These
functions are a huge aid in writing idempotent recipes and cookbooks.

rudeness
--------

Another thing to keep in mind is that some actions performed in recipes
can affect the end users of the systems, in effect being rude to them.
This might cause an outage or otherwise mess them up.  The recipe class
keeps track of whether or not this is ok in its ``ok_to_be_rude`` variable
so you can know what actions are acceptable.  Consult this before doing
rude things.

file set copying
----------------

The Recipe class defines a few helper functions for handling templates
and copying files to servers.  This is the primary way that recipes
interact with packages. They use the file set functions to copy the
package files and directories to the target server, processing their
contents in the process.

The routines run files with a ``.tmplt`` extension through Mako, using the
environment dictionary you pass to it.  Regular files just get copied.
You can specify owner, group, and permissions on a per-directory and
per-file basis using ``fck_metadata.txt`` files.  You can also have files
deleted from the target filesystem using ``fck_delete.txt`` files.

git repo checkouts
------------------

The Recipe class also defines some helper functions for working with git
repos.  You can checkout a git repo onto the remote machine, or check it
out locally and copy it to the remote machine if you don't want to setup
the remote machine to be able to do checkouts.

apply process
-------------

Several things happen when you apply a recipe to a server.  There are
two class methods that get called during the apply process, and possibly
two messages that get displayed.  Generally you'll just override the
apply method and sometimes add pre_apply or post_apply messages.  If you
override pre_apply_checks, remember to call the base class method.
Here's the order that things happen in:

pre_apply_message -> ``pre_apply_checks()`` -> ``apply()`` -> post_apply_message

Cookbooks
=========

Cookbooks are ordered lists of recipes to apply to a server to create
systems made up of subsystems.

Example::

    from frycook import Cookbook

    from recipes import RecipeHosts
    from recipes import RecipeRootUser
    from recipes import RecipeShorewall
    from recipes import RecipeSSH
    from recipes import RecipeFail2ban
    from recipes import RecipePostfix

    class CookbookBase(Cookbook):
        recipe_list = [RecipeRootUser,
                       RecipeHosts,
                       RecipeShorewall,
                       RecipeSSH,
                       RecipeFail2ban,
                       RecipePostfix]

There should be a cookbook list in the ``__init__.py`` file for the
cookbooks packge.  This lists all the cookbooks available to the
frycooker.py program.

Here's the ``__init__.py`` file for the sample cookbooks module::

    from base import CookbookBase
    from web import CookbookWeb

    cookbooks = {
        'base': CookbookBase,
        'web': CookbookWeb
        }

Packages Directory
==================

The packages directory contains all the files needed by the recipes.
There is one sub-directory per package, and each package generally
corresponds to a recipe.  Within each package the directories and files
are laid out the exact same as they will be on the target systems.  Any
files with ``.tmplt`` extensions will be processed as mako templates
before being copied out to computers.  The ``fck_metadata.txt`` files
define the ownership and permissions for the files and directories when
they're copied to the target system.  The ``fck_delete.txt`` files list
files that should be deleted in that directory on the target systems.

Here's the packages directory layout from our sample globule::

    packages                 # directory for the package files
      example_com            # root for example_com package files
        etc                  # corresponds to /etc on the target server
          nginx              # corresponds to /etc/nginx on the target server
            sites-available  # corresponds to /etc/nginx/sites-available on the target server
              example.com    # corresponds to /etc/nginx/sites-available/example.com on the target server
      hosts                  # root for hosts package files
        etc                  # corresponds to /etc on the target server
          hostname.tmplt     # template that becomes /etc/hostname on the target server
          hosts.tmplt        # template that becomes /etc/hosts on the target server
      nginx                  # root for nginx package files
        etc                  # corresponds to /etc directory on the target server
          default            # corresponds to /etc/default directory on the target server
            nginx            # corresponds to /etc/default/nginx file on the target server
          nginx              # corresponds to /etc/nginx directory on target server
            nginx.conf       # corresponds to /etc/nginx/nginx.conf file on target server
            sites-available  # corresponds to /etc/nginx/sites-available directory on target server
              default        # corresponds to /etc/nginx/sites-available/default directory on target server
              fck_delete.txt # lists files to delete from /etc/nginx/sites-available on target server
        srv                  # corresponds to /srv directory on the target server
          www                # corresponds to /srv/www directory on the target server
            50x.html         # corresponds to /srv/www/50x.html file on target server
            index.html       # corresponds to /srv/www/index.html file on target server
      postfix                # root for postfix package files
        etc                  # corresponds to /etc directory on the target server
          aliases            # corresponds to /etc/aliases directory on the target server
          mailname.tmplt     # template that becomes /etc/mailname on the target server
          postfix            # corresponds to /etc/postfix directory on the target server
            main.cf.tmplt    # template that becomes /etc/postfix/main.cf on the target server
      shorewall              # root for shorewall package files
        etc                  # corresponds to /etc directory on the target server
          default            # corresponds to /etc/default directory on the target server
            shorewall        # corresponds to /etc/default/shorewall directory on the target server
          shorewall          # corresponds to /etc/shorewall directory on the target server
            interfaces.tmplt # template that becomes /etc/shorewall/interfaces on the target server
      ssh                    # root for ssh package files
        etc                  # corresponds to /etc directory on the target server
          ssh                # corresponds to /etc/ssh directory on the target server
            sshd_config      # corresponds to /etc/ssh/sshd_config directory on the target server

template files
--------------

Template files have ``.tmplt`` extensions and are mako templates that are
prcoessed into their final form before being copied out to the
servers. They use the standard environment dictionary, plus any custom
dictionary entries prepared by the recipe.  Once processed, they are
copied with their filenames having having the ``.tmplt`` extension
removed.

Example::

    hosts.tmplt in package -> hosts on server

fck_delete.txt files
--------------------

``fck_delete.txt`` files list other files that should be deleted from the
targe directories, one filename per line.  You would have a separate
``fck_delete.txt`` file in each directory that you want files deleted
from.  The ``fck_delete.txt`` file itself is not copied.

fck_metadata.txt files
----------------------

``fck_metadata.txt`` files list the ownership and permissions you can set
on files in the directories, one line per file and/or directory. The
``fck_metadata.txt`` file itself is not copied.

regular files
-------------

Regular files are everything that's not a template file,
``fck_delete.txt`` file, or ``fck_metadata.txt`` file.  They are copied
verbatim to the server with no processing.

Settings
========

There are a few settings that frycook depends on.  They are read in from
a JSON file called ``settings.json`` and are passed around as a dictionary
to the constructors for Cookbooks and Recipes.  The settings dicionary
has the following keys:

``"package_dir"``: root of the packages hierarchy for the file copying
routines to look in

``"file_ignores"``: regex pattern for filenames to ignore while copying
package files

For any key containing the strings ``"dir"`` or ``"path"``, if you include a
tilde ``~`` in the value, it will be replaced with the home directory of
the user running frycooker.p, just like in bash.  For this example, that
would be the ``"package_dir"`` key.

Example settings.json file::

    {
        "package_dir": "~/Dropbox/dev/frycook/sample/packages/",
        "file_ignores": ".*~"
    }

Environment
===========

Frycook depends on having detailed knowledge of the metadata needed by
all the components when software is being setup on the computers.  It is
read in from a set of files into a single dictionary that is passed
around to the parts of the frycook framework.  The environment
dictionary contains all the metadata about the computers and the
environment they live in that frycooker.py, the recipes, and the
cookbooks need to function.  Most of its data is directly relevant to
specific recipes and is filled in depending on the recipes' needs.  It's
a dictionary with three main sections that should always be there:

``"users"``: a list of the users that recipes could reference, with such
things as public ssh keys

``"computers"``: a list of computers in the system, with such things as
ip addresses

``"groups"``: groups of computers that will be addressed as a unit

Just like for the settings dictionary, any key containing ``"dir"`` or
``"path"`` and including a tilde ``~`` in the value will have the tilde
replaced with the home directory of the user running frycooker.py.

Each computer in the ``"computers"`` section is also expected to have a
``"components"`` section listing all the cookbooks and recipes that that
computer uses.  This is used by frycooker.py to easily apply all
relevant cookbooks and recipes to computers.  It's also a good way to
keep track of what components make up that computer when it's fully
functional.

Each component in the list has a ``"type"`` key identifying if it's a
cookbook or a recipe, and a ``"name"`` key identifying the name of the
cookbook or recipe.

Example::

    {
        "computers": {
            "dev": {
                "components": [
                    {
                        "name": "base",
                        "type": "cookbook"
                    },
                    {
                        "name": "web",
                        "type": "cookbook"
                    }
                ],
                "domain_name": "fubu.example",
                "host_group": "dev",
                "private_ifaces": [
                    "eth2"
                ],
                "private_ips": {
                    "192.168.1.126": "dev"
                },
                "public_ifaces": [
                    "eth0",
                    "eth1"
                ],
                "public_ips": {
                    "192.168.56.10": "dev.fubu.example",
                    "192.168.56.11": "dev.fubu.example"
                }
            }
        },
        "groups": {
            "dev": {
                "computers": [
                    "dev"
                ]
            }
        },
        "users": {
            "example_com": {
                "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"
            },
            "root": {
                "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"
            }
        }
    }

This dictionary is created by processing the environment JSON files.
The main file is called ``environment.json``, and it can have include
directives that pull in additonal json files so that you can split up
large environments into multiple files.

environment.json::

    {
      "users": {
        "root": {
          "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"
        },
        "example_com": {
          "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"
        }
      },

      "computers": {
        "imports": ["comp_dev.json"]
      },

      "groups": {
        "dev" : {
          "computers": ["dev"]
        }
      }
    }

comp_dev.json::

    {
      "dev": {
        "domain_name": "fubu.example",
        "host_group": "dev",
        "public_ifaces": ["eth0", "eth1"],
        "public_ips": {"192.168.56.10": "dev.fubu.example",
                       "192.168.56.11": "dev.fubu.example"},
        "private_ifaces": ["eth2"],
        "private_ips": {"192.168.1.126": "dev"},
        "components": [{"type": "cookbook", "name": "base"},
                       {"type": "cookbook", "name": "web"}]
      }
    }

Frycooker.py
============

Frycooker.py is the program that takes all your carefully coded recipes
and cookbooks and applies them to computers.

The recipes and cookbooks modules should be accessible via the
``PYTHONPATH`` so they can be imported.  In the sample globule we ensure
this with the ``runner.sh`` wrapper script which sets up the python
path, then invokes frycooker.py::

    #!/bin/bash

    export PYTHONPATH=.
    frycooker.py $*

recipes and cookbooks vs. apply
-------------------------------

There are two ways to update computers.  The first way is to specify
recipes and cookbooks on the frycooker.py command line (using the '-r'
and '-c' command-line options) and have those be applied to all the
desired computers, in the order that they're specified.  This way is
nice to use when you have specific, small changes to apply.

The second way to update a computer is to use the *apply* option in
frycooker.py ('-a' command-line option).  With this option frycooker.py
looks at the ``"components"`` list in the environment for each specified
computer to determine what recipes and cookbooks apply to each computer,
then applies them.  This way is nice to use when you just want to bring
a computer into compliance with all of its components and don't want to
have to figure out which ones have changed and apply them individually.
This is when the idempotence of your recipes comes in handy because it
allows you to blindly update computers without worrying if the indicated
changes have already been applied.

computers vs. groups
--------------------

When choosing which computers to run frycook against, you have the
option of giving a list of computers or of specifying a group and having
frycooker.py run against all computers in that group.  Groups are
specified in the ``"groups"`` key in the environment json files.
Frycooker.py will use any combination of groups and computers that are
specified on its command line.  If there are identically named computers
and groups, the computer will be selected instead of the group.

messages
--------

Messages are text string that are printed out to the end-user of
frycooker.py either before or after a recipe or cookbook is run.
Frycooker.py agregates all message for the run and prints all the
pre-apply messages before anything is run and all the post-apply
messages after everything else has been run.  If you're curious as to
what messages a frycooker.py run will print, you can tell it to just
print the messages for you without applying any of the recipes or
cookbooks.

dry run
-------

You can do a dry run with frycooker.py to see what the final environment
dictionary will look like and what all computers things will be applied
to.  This is especially nice when you have lots of ``import`` directives
in your environment json files, or if you are applying things to a group
of machines.  This way you know how the environment imports are handled
and which computers frycooker.py thinks are in the group.

params
------

You can pass values into your recipes from the command-line using the
``--param`` command-line argument.  You can include multiple of these.
Frycooker will expect the arguments to be of the format
``<key>:<value>``.  These will be parsed and place into a dictionary in
the ``self.settings`` value in the recipe objects it creates, in a
sub-dictionary called ``params``.  You can see an example of how this is
used in the postfix recipe in the sample globule.
