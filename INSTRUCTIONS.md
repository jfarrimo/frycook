Frycook
=======

Frycook depends on recipes and cookbooks to define how systems are
built.  Recipes and cookbooks in turn use settings, environments, and
packages to do their work.  The settings and environments are passed
around as json-translatable dictionaries.  Packages live on disk as
directories and files.

Settings and environments exist as json-like dictionaries because they
are easy to turn into json files, and then read back from them, and
because most templating engines expect dictionaries to be passed to them
in order to render their contents.  This means that these dictionaries
map nicely to both the storage and rendering functions and keep frycook
simple.

settings dictionary
-------------------

There are a few settings that frycook depends on.  They're contained in
a dictionary called settings that's passed to the constructors for
Cookbooks and Recipes.  It has the following keys:

*package_dir*: root of the packages hierarchy for the file copying
routines to look in

*module_dir*: temporary directory for holding compiled mako modules
during template handling

*file_ignores*: regex pattern for filenames to ignore while copying
package files

*tmp_dir*: directory used to temporary hold files during some of the git
 repo manipulation routines in recipes

For any key containing 'dir' or 'path', if you include a tilde (~) in
the value, it will be replaced with the home directory of the user
running frycooker, just like in bash.  For this example, that would be
the "package_dir" and "module_dir" keys.

Example:

      {
      "package_dir": "~/bigawesomecorp/admin/packages/",
      "module_dir": "/tmp/bigawesomecorp/mako_modules",
      "tmp_dir": "/tmp",
      "file_ignores": ".*~"
      }

environment dictionary
----------------------

The environment dictionary contains all the metadata about the computers
and the environment they live in that the recipes and cookbooks need to
function.  Most of its data is directly relevant to specific recipes and
is filled in depending on the recipes' needs.  It's a dictionary with
three main sections that should always be there:

*users*: a list of the users that recipes could reference, with such
things as public ssh keys

*computers*: a list of computers in the system, with such things as ip
addresses

*groups*: groups of computers that will be addressed as a unit

Just like for the settings dictionary, any key containing 'dir' or
'path' and including a tilde (~) in the value will have the tilde
replaced with the home directory of the user running frycooker.

Each computer in the *computers* section is also expected to have a
*components* section listing all the cookbooks and recipes that that
computer uses.  This is used by frycooker to easily apply all relevant
cookbooks and recipes to computers.  It's also a good way to keep track
of what components make up that computer when it's fully functional.

Each component in the list has a *type* key identifying if it's a
cookbook or a recipe, and a *name* key identifying the name of the
cookbook or recipe.

Example:

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
        "test1": {
          "domain_name": "fubu.example",
          "host_group": "test",
          "public_ifaces": ["eth0", "eth1"],
          "public_ips": {"192.168.56.10": "test1.fubu.example",
                         "192.168.56.11": "test2.fubu.example"},
          "private_ifaces": ["eth2"],
          "private_ips": {"192.168.1.126": "test1"},
          "components": [{"type": "cookbook",
                          "name": "base"},
                         {"type": "cookbook",
                          "name": "web"}]
        }
      },

      "groups": {
        "test" : {
          "computers": ["test1"]
        }
      }
    }


packages directory
------------------

The packages directory contains all the files needed by the recipes.
There is one sub-directory per package, and each package generally
corresponds to a recipe.  Within each package the directories and files
are laid out the exact same as they will be on the target systems.  Any
files with .tmplt extensions will be processed as mako templates before
being copied out to computers.  The fck_metadata.txt files define the
ownership and permissions for the files and directories when they're
copied to the target system.  The fck_delete.txt files list files that
should be deleted in that directory on the target systems.

Here's an example layout:

    packages                 # directory for the package files
      hosts                  # root for hosts package files
        etc                  # corresponds to /etc on the target server
          hosts.tmplt        # template that becomes /etc/hosts on the target server
      nginx                  # root for nginx package files
        etc                  # corresponds to /etc directory on the target server
          default            # corresponds to /etc/default directory on the target server
            nginx            # corresponds to /etc/default/nginx file on the target server
          nginx              # corresponds to /etc/nginx directory on target server
            fck_metadata.txt # define ownership and perms for the /etc/nginx directory on the server
            nginx.conf       # corresponds to /etc/nginx/nginx.conf file on target server
            conf.d           # corresponds to /etc/nginx/conf.d directory on target server
            sites-available  # corresponds to /etc/nginx/sites-available directory on target server
              default        # corresponds to /etc/nginx/sites-available/default directory on target server
              fck_delete.txt # lists files to be deleted from the sites-available directory on target server
            sites-enabled    # corresponds to /etc/nginx/sites-enabled directory on target server
        srv                  # corresponds to /srv directory on the target server
          www                # corresponds to /srv/www directory on the target server
            50x.html         # corresponds to /srv/www/50x.html file on target server
            index.html       # corresponds to /srv/www/index.html file on target server

Recipes
=======

Recipes define subsystems that are distinct parts of larger systems.
They are the basic units of setup in frycook.  Generally a recipe
corresponds to a package that needs to be installed or configured.

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
keeps track of whether or not this is ok in its 'ok_to_be_rude' variable
so you can know what actions are acceptable.  Consult this before doing
rude things.

file set copying
----------------

The Recipe class defines a few helper functions for handling templates
and copying files to servers.  It runs files with a .tmplt extension
through Mako, using the dictionary you pass to it.  Regular files just
get copied.  You can specify owner, group, and permissions on a
per-directory and per-file basis.

git repo checkouts
------------------

The Recipe class also defines some helper functions for working with git
repos.  You can checkout a git repo onto the remote machine, or check it
out locally and copy it to the remote machine if you don't want to setup
the remote machine to be able to do checkouts.

apply process
-------------

This is where you apply a recipe to a server.  There are two class
methods that get called during the apply process, and possibly two
messages that get displayed.  Generally you'll just override the apply
method and sometimes add pre_apply or post_apply messages.  If you
override pre_apply_checks, remember to call the base class method.
Here's the order that things happen in:

pre_apply_message -> pre_apply_checks() -> apply() -> post_apply_message

Cookbooks
=========

Cookbooks are sets of recipes to apply to a server to create systems
made up of subsystems.

Frycooker
=========

Frycooker is the program that takes all your carefully coded recipes and
cookbooks and applies them to computers.

Pre-requisites
--------------

Frycooker depends on a few things to work properly.

** settings.json file **

Contains the settings for the program, in JSON format.

** environment.json file **

Contains the environment for the program, in JSON format.

** packages directory **

Contains all the package files for the recipes.

** recipes package **

This should be accessible via the PYTHONPATH so it can be imported.
There should be a recipe list in the __init__.py file for the packge.

** cookbooks package **

This should be accessible via the PYTHONPATH so it can be imported.
There should be a recipe list in the __init__.py file for the packge.

Globules
--------

All the files necessary for frycooker to run are usually arranged in a
directory structure that I call a *globule*.  Here's an example of
that::

    awesome_recipes           # root directory
      packages                # directory for the package files
        hosts                 # root for hosts package files
          etc                 # corresponds to /etc on the target server
            hosts.tmplt       # template that becomes /etc/hosts on the target
                              # server
        nginx                 # root for nginx package files
          etc                 # corresponds to /etc directory on the
                              # target server
            default           # corresponds to /etc/default directory on the
                              # target server
              nginx           # corresponds to /etc/default/nginx file on the
                              # target server
            nginx             # corresponds to /etc/nginx directory on target
                              # server
              nginx.conf      # corresponds to /etc/nginx/nginx.conf file on
                              # target server
              conf.d          # corresponds to /etc/nginx/conf.d directory on
                              # target server
              sites-available # corresponds to /etc/nginx/sites-available
                              # directory on target server
                default       # corresponds to /etc/nginx/sites-available/default
                              # directory on target server
              sites-enabled   # corresponds to /etc/nginx/sites-enable directory
                              # on target server
          srv                 # corresponds to /srv directory on the
                              # target server
            www               # corresponds to /srv/www directory on the target
                              # server
              50x.html        # corresponds to /srv/www/50x.html file on target
                              # server
              index.html      # corresponds to /srv/www/index.html file on target
                              # server
      setup                   # directory for non-package files
        runner.sh             # wrapper for frycooker that sets PYTHONPATH
        settings.json         # settings file
        environment.json      # environment file
        cookbooks             # directory to hold the cookbooks package
          __init__.py         # define the cookbook list here and import all
                              # cookbook classes
          base.py             # cookbook referencing all the recipes for a base
                              # server setup
          web.py              # cookbook for make a base server into a web server
        recipes               # directory to hold the recipes package
          __init__.py         # define the recipe list here and import all recipe
                              # classes
          root.py             # recipe for setting the root user's
                              # authorized_keys file
          hosts.py            # recipe for setting up the /etc/hosts file
          nginx.py            # recipe for setting up nginx
          example_com.py      # recipe for setting up example.com on a web server

----------------
Copyright (c) James Yates Farrimond. All rights reserved.

Redistribution and use in source and binary forms, with or without
Modification, are permitted provided that the following conditions are
met:

Redistributions of source code must retain the above copyright notice,
this list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright
notice, this list of conditions and the following disclaimer in the
documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY JAMES YATES FARRIMOND ''AS IS'' AND ANY
EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMES YATES FARRIMOND OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation
are those of the authors and should not be interpreted as representing
official policies, either expressed or implied, of James Yates
Farrimond.
