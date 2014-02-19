# Copyright (c) James Yates Farrimond. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# Modification, are permitted provided that the following conditions are met:
#
# Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY JAMES YATES FARRIMOND ''AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL JAMES YATES FARRIMOND OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are
# those of the authors and should not be interpreted as representing official
# policies, either expressed or implied, of James Yates Farrimond.

'''
Frycook depends on recipes and cookbooks to define how systems are built.
Recipes and cookbooks in turn use settings, environments, and packages to do
their work.  The settings and environments are passed around as dictionaries
and refer to the packages, which live on the disk as directories and files.

settings dictionary
===================

There are a few settings that frycook depends on.  They're contained in a
dictionary called settings that's passed to the constructors for Cookbooks and
Recipes.  It has the following keys:

I{package_dir}: root of the packages hierarchy for the file copying routines to
look in

I{module_dir}: temporary directory for holding compiled mako modules during
template handling

I{file_ignores}: regex pattern for filenames to ignore while copying package
files

For any key containing 'dir' or 'path', if you include a tilde (~) in the
value, it will be replaced with the home directory of the user running
frycooker, just like in bash.  For this example, that would be the
"package_dir" and "module_dir" keys.

example::

  {
  "package_dir": "~/bigawesomecorp/admin/packages/",
  "module_dir": "/tmp/bigawesomecorp/mako_modules",
  "tmp_dir": "/tmp",
  "file_ignores": ".*~"
  }

environment dictionary
======================

This contains all the metadata about the computers that the recipes and
cookbooks will be applied to.  Most of its data is directly relevant to
specific recipes and is filled in depending on the recipes' needs.  It's a
dictionary with three main sections that should always be there:

I{users}: a list of the users that recipes could reference, with such things as
public ssh keys

I{computers}: a list of computers in the system, with such things as ip
addresses

I{groups}: groups of computers that will be addressed as a unit

Just like for the settings dictionary, any key containing 'dir' or 'path' and
including a tilde (~) in the value will have the tilde replaced with the home
directory of the user running frycooker.

example::

  {
    "users": {
      "root": {
        "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"  # noqa
      },
      "example_com": {
        "ssh_public_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDYK8U9Isp+Ih+THCj2ohCo6nLY1R5Sn7oPzxM8ZBwH3ik/2EF3v0ibNezruja1I3OwF8W1QyWOdooIwTYJ8HXH9+Gyxcq/PseXbFWqg3k/lL50d5AawyRQZndOaNcFG6B8ULXJDksA6oQccXRzzxmnXpwGR8XEfSBCo2cdWDF1CXKvKXDZ4sqvGTVJIKshUAVbmfi4wH0LTtGIlV4IxslKUbfsErIU8kSyZNLLslq9XRvlqVK3iSabomKUY14MTbc3sefQzIctTtlmBpZw2mMBS49k4HYo1UwhUNiLbFBS7QhcivbJwFqGPj0N5pAx0oPUj1m96GGsqpiqu1eNp/yb jay@Jamess-MacBook-Air.local"  # noqa
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
        "private_ips": {"192.168.1.126": "test1"}
      }
    },

    "groups": {
      "test" : {
        "computers": ["test1"]
      }
    }
  }


packages directory
==================

This contains all the files needed by the recipes.  There is one sub-directory
per package, and each package generally corresponds to a recipe.  Within each
package the directories and files are laid out the exact same as they will be
on the target systems.  Any files with .tmplt extensions will be processed as
mako templates before being copied out to computers.  The fck_metadata.txt
files define the ownership and permissions for the files and directories when
they're copied to the target system.  Here's an example layout::

    packages                 # directory for the package files
      hosts                  # root for hosts package files
        etc                  # corresponds to /etc on the target server
          hosts.tmplt        # template that becomes /etc/hosts on the target
                             # server
      nginx                  # root for nginx package files
        etc                  # corresponds to /etc directory on the
                             # target server
          default            # corresponds to /etc/default directory on the
                             # target server
            nginx            # corresponds to /etc/default/nginx file on the
                             # target server
          nginx              # corresponds to /etc/nginx directory on target
                             # server
            fck_metadata.txt # define ownership and perms for the /etc/nginx
                             # directory on the server
            nginx.conf       # corresponds to /etc/nginx/nginx.conf file on
                             # target server
            conf.d           # corresponds to /etc/nginx/conf.d directory on
                             # target server
            sites-available  # corresponds to /etc/nginx/sites-available
                             # directory on target server
              default        # corresponds to
                             # /etc/nginx/sites-available/default
                             # directory on target server
            sites-enabled    # corresponds to /etc/nginx/sites-enable directory
                             # on target server
        srv                  # corresponds to /srv directory on the
                             # target server
          www                # corresponds to /srv/www directory on the target
                             # server
            50x.html         # corresponds to /srv/www/50x.html file on target
                             # server
            index.html       # corresponds to /srv/www/index.html file on
                             # target server

============

Copyright (c) James Yates Farrimond. All rights reserved.

Redistribution and use in source and binary forms, with or without
Modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this
list of conditions and the following disclaimer in the documentation and/or
other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY JAMES YATES FARRIMOND ''AS IS'' AND ANY EXPRESS OR
IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
EVENT SHALL JAMES YATES FARRIMOND OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of James Yates Farrimond.
'''
from cookbook_template import Cookbook  # noqa
from recipe_template import Recipe, RecipeException  # noqa

__version__ = '0.3.3'
