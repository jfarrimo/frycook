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
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN 
# NO EVENT SHALL JAMES YATES FARRIMOND OR CONTRIBUTORS BE LIABLE FOR ANY 
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF 
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are 
# those of the authors and should not be interpreted as representing official 
# policies, either expressed or implied, of James Yates Farrimond.

'''
Frycook depends on several things.  You'll see these things
passed to the classes and referenced from the classes.

settings dict
=============

There are a few settings that frycook depends on.  They're
contained in a dictionary called settings that's passed
to the constructors for Cookbooks and Recipes.  It has the
following keys:

I{package_dir}: root of the packages hierarchy for the file
copying routines to look in

I{module_dir}: temporary directory for holding compiled mako
modules during template handling

I{file_ignores}: file patterns to ignore while copying package
files

environment dict
================

This contains all the metadata about the computers
the recipes and cookbooks will be applied to.  Most of its
data is directly relevant to specific recipes and is
filled in depending on the recipes' needs.  It's a 
dictionary with three main sections that should always
be there:

I{users}: a list of the users recipes could reference, with such
things as public ssh keys and email addresses for them

I{computers}: a list of computers in the system, with such things
as ip addresses

I{groups}: groups of computers that will be addressed as a unit

example::

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
      "public_ifaces": ["eth1"],
      "public_ips": {"172.20.10.14": "test1.fubu.example"},
      "private_ifaces": ["eth0"],
      "private_ips": {"192.168.56.10": "test1"}
    }
  },

  "groups": {
    "test" : {
      "computers": ["test1"]
    }
  }


packages directory
==================

This contains all the files needed by the recipes.  These are 
laid out the exact same as they will be on the target systems.
Any files with a .tmplt extension will be processed as mako
templates before being copied out to computers.  Here's an 
example layout::

    packages                # directory for the package files
      hosts                 # root for hosts package files
        etc                 # corresponds to /etc on the target server
          hosts.tmplt       # template that becomes /etc/hosts on the target server
      nginx                 # root for nginx package files
        etc                 # corresponds to /etc directory on the target server
          default           # corresponds to /etc/default directory on the target server
            nginx           # corresponds to /etc/default/nginx file on the target server
          nginx             # corresponds to /etc/nginx directory on target server
            nginx.conf      # corresponds to /etc/nginx/nginx.conf file on target server
            conf.d          # corresponds to /etc/nginx/conf.d directory on target server
            sites-available # corresponds to /etc/nginx/sites-available directory on target server
              default       # corresponds to /etc/nginx/sites-available/default directory on target server
            sites-enabled   # corresponds to /etc/nginx/sites-enable directory on target server
        srv                 # corresponds to /srv directory on the target server
          www               # corresponds to /srv/www directory on the target server
            50x.html        # corresponds to /srv/www/50x.html file on target server
            index.html      # corresponds to /srv/www/index.html file on target server

============

Copyright (c) James Yates Farrimond. All rights reserved.

Redistribution and use in source and binary forms, with or without 
Modification, are permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this 
list of conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, 
this list of conditions and the following disclaimer in the documentation 
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY JAMES YATES FARRIMOND ''AS IS'' AND ANY EXPRESS 
OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES 
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN 
NO EVENT SHALL JAMES YATES FARRIMOND OR CONTRIBUTORS BE LIABLE FOR ANY 
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES 
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; 
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT 
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF 
THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are 
those of the authors and should not be interpreted as representing official 
policies, either expressed or implied, of James Yates Farrimond.
'''
from cookbook_template import Cookbook
from recipe_template import Recipe, RecipeException
