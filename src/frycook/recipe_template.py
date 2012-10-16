'''
Recipes are the basic units of setup in frycook.  Generally a
recipe corresponds to a package that needs to be installed
or a subsystem that needs to be configured.

Generally recipes are written to be idempotent so that they
can be run over and over again on a server with no adverse
effects.
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
