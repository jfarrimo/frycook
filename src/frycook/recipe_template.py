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
Recipes are the basic units of setup in frycook.  Generally a
recipe corresponds to a package that needs to be installed
or a subsystem that needs to be configured.

idempotence
===========

One thing to keep in mind when creating recipes and cookbooks 
is idempotency.  By keeping idempotency in mind in general 
you can create recipes that you can run again and again to 
push out minor changes to a package.  This way your recipes 
become the only way that you modify your servers and can be 
a single chokepoint that you can monitor to make sure things 
happen properly.

Lots of the cuisine functions you'll use have an "ensure" 
version that first checks to see if a condition is true 
before applying it, such as checking if a package is 
installed before trying to install it.  This is nice when 
things could cause undesired configuration changes or 
expensive operations that you don't want to happen every 
time.  These functions are a huge aid in writing idempotent 
recipes and cookbooks.


apply
=====

This is where you apply a recipe to a server.  There are 
two class methods that get called during the apply process. 
Generally you'll just override the apply method.  If you 
override pre_apply_checks, remember to call the base class 
method.  Here's the order that functions get called:

pre_apply_checks -> apply

cleanup
=======

This is where you cleanup old recipe configurations from a 
server.  An example is when I changed the home directory for 
my web server.  I first wrote a cleanup that cleaned-up the 
old configuration, then an apply to apply the new 
configuration.  That way you can always run the apply in the 
future when building new machines and don't need the cleanup 
logic since the new machine never had the old configuration 
that had to get cleaned-up.

file set copying
================

The Recipe class defines a few helper functions for handling 
templates and copying files to servers.  It runs files with
a .tmplt extension through make using the dictionary you 
pass to it.  Regular files just get copied.
'''
import os
import os.path
import re

import cuisine
from mako.lookup import TemplateLookup

class RecipeException(Exception):
    '''
    Exception raised for exceptional conditions encountered
    while using the Recipe class.
    '''
    pass

class Recipe(object):
    '''
    Base object for all recipes to subclass.  It defines the
    framework for recipes and some helper functions.  By itself
    it doesn't do much.
    '''

    def __init__(self, settings, environment):
        '''
        @type settings: dict
        @param settings: settings dictionary
        @type environment: dict
        @param environment: metadata dictionary
        '''
        self.settings = settings
        self.environment = environment
        self.mylookup = TemplateLookup(
            directories=[self.settings["package_dir"]], 
            module_directory=self.settings["module_dir"])

    #######################
    ######## APPLY ########
    #######################

    def pre_apply_checks(self, computer):
        '''
        Define checks to run before applying the recipe.  The
        base class checks that the designated computer exists
        in the environment dictionary.  This is a good place
        to check other things in your environment dictionary
        that the apply function expects to be there.  Override
        this function in your subclass of Recipe if you have
        any checks to perform.  Be sure to call the base class
        function to make sure its checks get done as well.

        @type computer: string
        @param computer: computer to apply recipe checks to
        @raise RecipeException: raised if the computer name is not in the environment being processed
        '''
        # make sure the computer is in our enviro
        if computer not in self.environment["computers"]:
            raise RecipeException(
                "computer %s not defined in environment" % computer)

    def apply(self, computer):
        '''
        Define the actions to take place when this recipe is
        applied to a computer.  Override this function in your 
        subclass of Recipe if you have any actions to apply.
        If you don't have any actions, then why are you creating
        a recipe?

        @type computer: string
        @param computer: computer to apply recipe to
        '''
        pass

    def run_apply(self, computer):
        '''
        Run the apply sequence of functions.  This is typically
        called by frycooker.

        @type computer: string
        @param computer: computer to apply recipe to
        '''
        self.pre_apply_checks(computer)
        self.apply(computer)

    #########################
    ######## CLEANUP ########
    #########################

    def cleanup(self, computer):
        ''' 
        Define cleanup actions that need to be taken on the
        designated computer.  Override this function in your
        sub-class of Recipe to do things.

        @type computer: string
        @param computer: computer to apply recipe cleanup to
        '''
        pass

    def run_cleanup(self, computer):
        ''' 
        Run the cleanup function.  This is typically
        called by frycooker. 

        @type computer: string
        @param computer: computer to apply recipe cleanup to
        '''
        self.cleanup(computer)

    ###############################
    ######## FILE HANDLING ########
    ###############################

    def push_file(self, local_name, remote_name):
        ''' 
        Copy a file to a remote server if the file is
        different or doesn't exist.

        @type local_name: string
        @param local_name: path within packages dir of file to upload (path + filename)
        @type remote_name: string
        @param remote_name: remote path to write file to (path + filename)
        '''
        cuisine.file_upload(remote_name, 
                            os.path.join(self.settings["package_dir"], 
                                         local_name))

    def push_template(self, templatename, out_path, enviro):
        ''' 
        Process a template file and push its contents
        to a remote server if it's different than what's
        already there.

        @type templatename: string
        @param templatename: path within packages dir of template file to process (path + filename)
        @type out_path: string
        @param out_path: path on remote server to write file to (path + filename)
        @type enviro: dict
        @param enviro: environment dictionary for template engine
        '''
        mytemplate = self.mylookup.get_template(templatename)
        buff = mytemplate.render(**enviro)
        cuisine.file_write(out_path, buff, check=True)

    def push_package_file_set(self, package_name, template_env):
        ''' 
        Copy a set of files to a remote server, maintaining
        the same directory structure and processing any templates
        it encounters.

        This copies the files to the root of the destination,
        so that things like /etc/hosts or /etc/nginx/nginx.conf
        get put in the right place.  Just create a directory
        structure that mirrors the target machine and all files
        will get copied there in the correct place.

        @type package_name: string
        @param package_name: name of package to process, corresponds to directory in packages directory
        @type template_env: dict
        @param template_env: environment dictionary for template engine
        '''
        work_dir = os.path.join(self.settings["package_dir"], 
                                package_name)
        os.chdir(work_dir)
        for root, dirs, files in os.walk('.'):
            for f in files:
                filename = os.path.join(root, f).lstrip('./')
                if re.search(self.settings["file_ignores"], filename) is None:
                    base_path, ext = os.path.splitext(filename)
                    if ext == '.tmplt':
                        self.push_template(os.path.join(package_name, filename),
                                           os.path.join('/', base_path),
                                           template_env)
                    else:
                        self.push_file(os.path.join(work_dir, filename),
                                       os.path.join('/', filename))
