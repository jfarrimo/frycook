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
Recipes define subsystems that are distinct parts of larger systems.  They are
the basic units of setup in frycook.  Generally a recipe corresponds to a
package that needs to be installed or configured.

idempotence
===========

One thing to keep in mind when creating recipes and cookbooks is idempotency.
By keeping idempotency in mind in general you can create recipes that you can
run again and again to push out minor changes to a package.  This way your
recipes become the only way that you modify your servers and can be a single
chokepoint that you can monitor to make sure things happen properly.

Lots of the cuisine functions you'll use have an "ensure" version that first
checks to see if a condition is true before applying it, such as checking if a
package is installed before trying to install it.  This is nice when things
could cause undesired configuration changes or expensive operations that you
don't want to happen every time.  These functions are a huge aid in writing
idempotent recipes and cookbooks.

rudeness
========

Another thing to keep in mind is that some actions performed in recipes can
affect the end users of the systems, in effect being rude to them.  This might
cause an outage or otherwise mess them up.  The recipe class keeps track of
whether or not this is ok in its 'ok_to_be_rude' variable so you can know what
actions are acceptable.  Consult this before doing rude things.

file set copying
================

The Recipe class defines a few helper functions for handling templates and
copying files to servers.  It runs files with a .tmplt extension through Mako,
using the dictionary you pass to it.  Regular files just get copied.  You can
specify owner, group, and permissions on a per-directory and per-file basis.

git repo checkouts
==================

The Recipe class also defines some helper functions for working with git repos.
You can checkout a git repo onto the remote machine, or check it out locally
and copy it to the remote machine if you don't want to setup the remote machine
to be able to do checkouts.

apply process
=============

This is where you apply a recipe to a server.  There are two class methods that
get called during the apply process, and possibly two messages that get
displayed.  Generally you'll just override the apply method and sometimes add
pre_apply or post_apply messages.  If you override pre_apply_checks, remember
to call the base class method.  Here's the order that things happen in:

pre_apply_message -> pre_apply_checks() -> apply() -> post_apply_message
'''
import os
import os.path
import re
import shutil
import stat

import cuisine
from fabric.api import local
from mako.lookup import TemplateLookup


class RecipeException(Exception):
    '''
    A RecipeException exception is raised for exceptional conditions
    encountered while using the Recipe class.
    '''
    pass


class FileMetaDataTracker(object):
    '''
    A FileMetaDataTracker object keeps track of owner, group, and permissions
    for files and directories during a push_package_fileset operation.  This
    hinges on a file named fck_metadata.txt being encountered in the directory
    being examined.  This file should have each line contain the text
    <filename>:<owner>:<group>:<perms>, where <filename> is either a file name
    or '.' for the directory itself, <owner> is the owner's account name,
    <group> is the group's name, and <perms> is the permissions string..
    '''

    tagfile = 'fck_metadata.txt'

    def __init__(self):
        '''
        Start with a blank metadata dictionary.
        '''
        self.metadata = {}

    def check_directory(self, root, dirs, files):
        '''
        Read in the metadata for the given directory from the fck_metadata.txt
        file in the directory, or remember metadata from previous calls if no
        fck_metadata.txt file is encountered.

        The input parameters are expected to be the values returned from a call
        to os.walk()

        @type root: string

        @param root: directory being examined

        @type dirs: list of strings

        @param dirs: list of sub-directories under the root directory

        @type files: list of strings

        @param files: list of the files in the root directory
        '''
        if root not in self.metadata:
            self.metadata[root] = (None, None, None, )

        if self.tagfile in files:
            for line in open(os.path.join(root, self.tagfile)):
                parts = line.split(':')
                path = parts[0].strip()
                if len(path) > 0 and path[0] != '#':
                    owner = parts[1].strip()
                    group = parts[2].strip()
                    if len(parts) > 3:
                        perms = parts[3].strip()
                    else:
                        perms = None

                    if path == '.':
                        self.metadata[root] = (owner, group, perms, )
                        for dn in dirs:
                            self.metadata[os.path.join(root, dn)] = (
                                owner, group, perms, )
                    else:
                        self.metadata[os.path.join(root, path)] = (
                            owner, group, perms, )

    def get_metadata(self, path, filename=''):
        '''
        Get the owner, group, and permissions for the given path and filename.
        If no filename is specified, the data is retrieved for the directory
        specified in path.

        @type path: string

        @param path: path to file to get metadata for

        @type filename: string

        @param filename: name of file to get metadata for (leave blank if just
        getting directory metadata)

        @rtype: tuple of strings

        @return: tuple containing (<owner>, <group>, <perms>, )
        '''
        fq = os.path.join(path, filename)
        if fq in self.metadata:
            return self.metadata[fq]
        elif path in self.metadata:
            return self.metadata[path]
        else:
            return None, None, None


class FileDeleter(object):
    '''
    A FileDeleter object deletes unwanted files from a directory.  This hinges
    on a file named fck_delete.txt being encountered in the directory being
    examined.  This file should have each line contain the name of a file to be
    deleted.
    '''

    tagfile = 'fck_delete.txt'

    def check_directory(self, root, files, remote_rootpath):
        '''
        Examine the given directory, check for a fck_delete.txt file in the
        directory, and delete all files named in fck_delete.txt.

        The first of the input parameters are expected to be values returned
        from a call to os.walk()

        @type root: string

        @param root: directory being examined

        @type files: list of strings

        @param files: list of the files in the root directory

        @type remote_rootpath: string

        @param remote_rootpath: path on remote server to delete files from
        '''

        if self.tagfile in files:
            for line in open(os.path.join(root, self.tagfile)):
                delfile = os.path.join(remote_rootpath, line.strip())
                cuisine.file_unlink(delfile)


class Recipe(object):
    '''
    The Recipe class is the base class for all recipes to subclass.  It defines
    the framework for recipes and some helper functions.  By itself it doesn't
    do much.

    Here is an example that implements a basic recipe to make sure a package is
    installed::

      import cuisine

      from frycook import Recipe

      class RecipeFail2ban(Recipe):
          def apply(self, computer):
              cuisine.package_ensure('fail2ban')

    All recipe files should live in a single recipes package.  The __init__.py
    file for this package should import all recipes and have a list of them so
    they can easily be imported by the frycooker program.

    Example::

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
    '''

    def __init__(self, settings, environment, ok_to_be_rude, no_prompt):
        '''
        Initialize the recipe object with the settings and environment
        dictionaries.

        @type settings: dict

        @param settings: settings dictionary

        @type environment: dict

        @param environment: metadata dictionary

        @type ok_to_be_rude: boolean

        @param ok_to_be_rude: is it ok to interrupt your users?

        @type no_prompt: boolean

        @param no_prompt: should we prompt the user?
        '''
        self.settings = settings
        self.environment = environment
        self.ok_to_be_rude = ok_to_be_rude
        self.no_prompt = no_prompt
        self.mylookup = TemplateLookup(
            directories=[self.settings["package_dir"]],
            module_directory=self.settings["module_dir"])

    #######################
    ######## APPLY ########
    #######################

    pre_apply_message = ""

    def handle_pre_apply_message(self):
        '''
        Print the pre-apply message for the user and wait for him/her to hit
        return before continuing.
        '''
        if self.pre_apply_message:
            header = "pre-apply message from %s:" % self.__class__.__name__
            print '=' * len(header)
            print header
            print '=' * len(header)
            print self.pre_apply_message
            if not self.no_prompt:
                raw_input('press enter to continue')

    post_apply_message = ""

    def handle_post_apply_message(self):
        '''
        Print the post-apply message for the user and wait for him/her to hit
        return before continuing.
        '''
        if self.post_apply_message:
            header = "post-apply message from %s:" % self.__class__.__name__
            print '=' * len(header)
            print header
            print '=' * len(header)
            print self.post_apply_message
            if not self.no_prompt:
                raw_input('press enter to continue')

    def pre_apply_checks(self, computer):
        '''
        Define checks to run before applying the recipe.  The base class checks
        that the designated computer exists in the environment dictionary.
        This is a good place to check other things in your environment
        dictionary that the apply function expects to be there.  Override this
        function in your subclass of Recipe if you have any checks to perform.
        Raise a RecipeException if you encounter exceptional conditions.  Be
        sure to call the base class function to make sure its checks get done
        as well.

        @type computer: string

        @param computer: computer to apply recipe checks to

        @raise RecipeException: raised if the computer name is not in the
        environment being processed
        '''
        # make sure the computer is in our enviro
        if computer not in self.environment["computers"]:
            raise RecipeException(
                "computer %s not defined in environment" % computer)

    def apply(self, computer):
        '''
        Define the actions to take place when this recipe is applied to a
        computer.  Override this function in your subclass of Recipe if you
        have any actions to apply.  If you don't have any actions, then why are
        you creating a recipe?

        @type computer: string

        @param computer: computer to apply recipe to
        '''
        pass

    def run_apply(self, computer):
        '''
        Run the apply sequence of functions.  This is typically called by
        frycooker.

        Sequence::

          pre_apply_message -> pre_apply_checks() -> apply() -> post_apply_message

        @type computer: string

        @param computer: computer to apply recipe to
        '''
        self.pre_apply_checks(computer)
        self.apply(computer)

    def run_messages(self):
        '''
        Print the pre and post apply messages only, as if the apply had been
        run.
        '''
        self.handle_pre_apply_message()
        self.handle_post_apply_message()

    ###############################
    ######## FILE HANDLING ########
    ###############################

    def get_local_file_perms(self, local_name):
        '''
        Get a string of the permissions set on a local file.

        @type local_name: string

        @param local_name: path to file on local file system

        @rtype: string

        @return: string containing perms of file, ie. '655'
        '''
        bit_mode = stat.S_IMODE(os.stat(local_name).st_mode)
        user_perms = (bit_mode & stat.S_IRWXU) >> 6
        group_perms = (bit_mode & stat.S_IRWXG) >> 3
        other_perms = bit_mode & stat.S_IRWXO
        string_perms = "%s%s%s" % (user_perms, group_perms, other_perms)
        return string_perms

    def push_file(self, local_name, remote_name, owner, group, perms=None):
        '''
        Copy a file to a remote server if the file is different or doesn't
        exist.

        @type local_name: string

        @param local_name: path within packages dir of file to upload (path +
        filename)

        @type remote_name: string

        @param remote_name: remote path to write file to (path + filename)

        @type owner: string

        @param owner: owner of the file

        @type group: string

        @param group: group of the file

        @type perms: string

        @param perms: permissions for the file
        '''
        local_name = os.path.join(self.settings["package_dir"], local_name)
        cuisine.file_upload(remote_name, local_name)
        if not perms:
            perms = self.get_local_file_perms(local_name)
        cuisine.file_attribs(
            remote_name, mode=perms, owner=owner, group=group)

    def push_template(self, templatename, out_path, enviro,
                      owner, group, perms=None):
        '''
        Process a template file and push its contents to a remote server if
        it's different than what's already there.

        @type templatename: string

        @param templatename: path within packages dir of template file to
        process (path + filename)

        @type out_path: string

        @param out_path: path on remote server to write file to (path +
        filename)

        @type enviro: dict

        @param enviro: environment dictionary for template engine

        @type owner: string

        @param owner: owner of the templated file

        @type group: string

        @param group: group of the templated file

        @type perms: string

        @param perms: permissions for the templated file
        '''
        mytemplate = self.mylookup.get_template(templatename)
        try:
            buff = mytemplate.render(**enviro)
        except Exception, e:
            raise RecipeException(
                "Error rendering template %s: %s" % (templatename, e))
        cuisine.file_write(out_path, buff, check=True)
        local_name = os.path.join(self.settings["package_dir"], templatename)
        if not perms:
            perms = self.get_local_file_perms(local_name)
        cuisine.file_attribs(
            out_path, mode=perms, owner=owner, group=group)

    def _push_package_file_set(self, package_name, template_env):
        '''
        Implement the file copying and deleting portion of the
        push_package_file_set operation.  The calling function sets up the
        template environment, then calls this one.

        @type package_name: string

        @param package_name: name of package to process, corresponds to
        directory in packages directory

        @type template_env: dict

        @param template_env: environment dictionary for template engine
        '''
        metadata = FileMetaDataTracker()
        deleter = FileDeleter()
        work_dir = os.path.join(self.settings["package_dir"], package_name)
        os.chdir(work_dir)
        for root, dirs, files in os.walk('.'):
            metadata.check_directory(root, dirs, files)
            owner, group, perms = metadata.get_metadata(root)
            remote_root = '/'+root.lstrip('.')
            cuisine.dir_ensure(
                remote_root, owner=owner, group=group, mode=perms)
            for filename in files:
                fq_filename = os.path.join(remote_root, filename).lstrip('/')
                if (re.search(self.settings["file_ignores"], filename) is None
                        and filename != metadata.tagfile
                        and filename != deleter.tagfile):
                    owner, group, perms = metadata.get_metadata(root, filename)
                    base_path, ext = os.path.splitext(fq_filename)
                    if ext == '.tmplt':
                        self.push_template(os.path.join(package_name,
                                                        fq_filename),
                                           os.path.join('/', base_path),
                                           template_env, owner, group, perms)
                    else:
                        self.push_file(os.path.join(work_dir, fq_filename),
                                       os.path.join('/', fq_filename),
                                       owner, group, perms)
            deleter.check_directory(root, files, remote_root)

    def push_package_file_set(self, package_name, computer_name, aux_env=None):
        '''
        Copy a set of files to a remote server, maintaining the same directory
        structure and processing any templates encountered. This copies the
        files to the root of the destination, so that things like /etc/hosts or
        /etc/nginx/nginx.conf get put in the right place.

        First create a directory with the same name as package_name in your
        root packages directory.  Then create a directory structure under that
        that mirrors the target machine and all files will get copied there in
        the correct place.

        For template file processing, a default environment dictionary will be
        passed in consisting of::

          {"computer": host_env["computers"][computer_name]}

        Template files have a .tmplt extension.

        If aux_env is given, it will be added to the default dictionary using
        dict.update() after the default dictionary is constructed.  This means
        that if you pass in an aux_env dictionary with a key called "computer",
        that that key will over-write the default key of that name.

        If a file named fck_metadata.txt is encountered in a directory, then
        it's expected to have contents of lines consisting of
        <path>:<owner>:<group>:<perms> that specifies the owner, group, and
        permissions for the path specified (directory-relative).

        If a file named fck_delete.txt is encountered in a directory, then it's
        expected to have contents of lines containing names of files to delete,
        one per line.  This way you can clean out a directory as well as copy
        files to it.

        @type package_name: string

        @param package_name: name of package to process, corresponds to
        directory in packages directory

        @type template_env: dict

        @param template_env: environment dictionary for template engine

        @type aux_env: dict

        @param aux_env: additional key/value pairs for the template environment
        '''
        template_env = {"computer":
                        self.environment["computers"][computer_name]}
        if aux_env is not None:
            template_env.update(aux_env)
        self._push_package_file_set(package_name, template_env)

    ##############################
    ######## GIT HANDLING ########
    ##############################

    def push_git_repo(self, computer, user, group, git_url, target_path):
        '''
        Make a local clone of the repo in git_url into the temp directory
        specified in the settings file, then rsync it to the remote path.

        @type computer: string

        @param computer: computer name to push to

        @type user: string

        @param user: user to own the files in the repo

        @type group: string

        @param group: group to own the files in the repo

        @type git_url: string

        @param git_url: git url of repo (probably from github)

        @type target_path: string

        @param target_path: root path on remote server to copy git repo to
        '''
        rsync_command = ('rsync -qrlptz --delete --delete-excluded '
                         '--exclude=.svn --exclude=.git')
        tmp_path = os.path.join(self.settings["tmp_dir"],
                                'push_git_repo/repo/')
        if not os.path.exists(tmp_path):
            local('git clone %s %s' % (git_url, tmp_path))
        else:
            local('cd %s && git pull' % tmp_path)
        local('%s %s root@%s:%s' %
              (rsync_command, tmp_path, computer, target_path))
        cuisine.sudo('chown -R %s:%s %s' % (user, group, target_path))
        shutil.rmtree(tmp_path)

    def clone_git_repo(self, user, git_url, target_path):
        '''
        Clone a git repo on a remote server.

        @type git_url: string

        @param git_url: git url of repo (probably from github)

        @type target_path: string

        @param target_path: root path on remote server to clone git repo into
        '''
        cuisine.sudo('sudo -Hi -u %s git clone %s %s' %
                     (user, git_url, target_path))

    def update_git_repo(self, user, git_url, target_path):
        '''
        Update an existing git repo on a remote server.

        @type git_url: string

        @param git_url: git url of repo (probably from github)

        @type target_path: string

        @param target_path: root path on remote server to update git repo in
        '''
        cuisine.sudo('cd %s && sudo -u %s git pull' % (target_path, user))

    def is_git_repo(self, target_path):
        '''
        Make sure a git repo exists on the remote computer and is really
        a git repo.

        @type git_url: string

        @param git_url: git url of repo (probably from github)

        @type target_path: string

        @param target_path: root path on remote server to check git repo

        @rtype: boolean

        @return: True if repo already existed, False if not

        '''
        if not cuisine.dir_exists(os.path.join(target_path, '.git')):
            return False
        ret = cuisine.sudo('cd %s && git status' % target_path)
        if not ret.succeeded:
            return False
        return True

    def ensure_git_repo(self, user, git_url, target_path):
        '''
        Make sure a git repo exists on the remote computer.

        @type git_url: string

        @param git_url: git url of repo (probably from github)

        @type target_path: string

        @param target_path: root path on remote server to check git repo

        @rtype: boolean

        @return: True if repo already existed, False if not
        '''
        if not cuisine.dir_exists(target_path):
            self.clone_git_repo(user, git_url, target_path)
            return False
        return True
