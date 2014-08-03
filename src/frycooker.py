#!/env/python

# Copyright (c) James Yates Farrimond. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# Modification, are permitted provided that the following conditions are
# met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY JAMES YATES FARRIMOND ''AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL JAMES YATES FARRIMOND OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation
# are those of the authors and should not be interpreted as representing
# official policies, either expressed or implied, of James Yates
# Farrimond.

'''
Frycooker is the program that takes all your carefully coded recipes and
cookbooks and applies them to computers.
'''

import argparse
import json
import os
import sys

import cuisine
from fabric.api import env
from fabric.network import disconnect_all

import cookbooks
import recipes


def get_args():
    '''
    Parse the command-line arguments, using python's argparse library.

    :rtype: argparse args object
    :return: object containing attributes for all possible command-line arguments
    '''
    recipe_names = recipes.recipes.keys()
    recipe_names.sort()
    cookbook_names = cookbooks.cookbooks.keys()
    cookbook_names.sort()

    parser = argparse.ArgumentParser(description='Setup machines.')
    parser.add_argument('-a', '--apply', action='store_true', default=False,
                        help='apply components to named servers')
    parser.add_argument('-c', '--cookbook', dest='cookbooks', action='append',
                        choices=cookbook_names,
                        help='cookbook to process (can specify multiple times)'
                        )
    parser.add_argument('-d', '--dryrun', action='store_true', default=False,
                        help='do not apply actions, just verify environment '
                        'and see which hosts to apply to')
    parser.add_argument('-e', '--environment', default='environment.json',
                        help='environment file')
    parser.add_argument('-m', '--messages', action='store_true', default=False,
                        help='do not apply actions, just print messages')
    parser.add_argument('-n', '--no-prompt', action='store_true', default=False,
                        dest='no_prompt', help='do not prompt user for '
                        'anything; good for automated scripts')
    parser.add_argument('-O', '--ok-to-be-rude', action='store_true',
                        default=False, dest='ok_to_be_rude',
                        help='ok to be rude to your users')
    parser.add_argument('-p', '--package-update', action='store_true',
                        default=False, dest='package_update',
                        help='update the package manager before '
                        'applying recipes/cookbooks')
    parser.add_argument('-r', '--recipe', dest='recipes', action='append',
                        choices=recipe_names,
                        help='recipe to process (can specify multiple times)')
    parser.add_argument('-s', '--settings', default='settings.json',
                        help='settings file')
    parser.add_argument('-u', '--user', default='root',
                        help='user to ssh to host as')
    parser.add_argument('target', nargs='+',
                        help='computer or group to apply setup to')

    args = parser.parse_args()
    return args


def massage_enviro_paths(env):
    '''
    Recursively iterate through all the keys in the environment
    dictionary and look for any that contain the strings 'path' or 'dir'
    in them.  For the values corresponding to the keys that do, replace
    any instances of the '~' character with the running user's home
    directory path.

    :type env: dictionary
    :param env: environment dictionary
    '''
    for k, v in env.iteritems():
        if isinstance(v, dict):
            massage_enviro_paths(v)
        elif (isinstance(k, basestring) and
              isinstance(v, basestring) and
              (k.find('path') > -1 or k.find('dir') > -1)):
            env[k] = v.replace('~', os.environ['HOME'])


def load_settings(filename):
    '''
    Load the settings json file, massaging its environment paths in the
    process.

    :type filename: string
    :param filename: filename of settings file to read

    :rtype: dictionary
    :return: dictionary representation of settings
    '''
    settings = json.load(open(filename))
    massage_enviro_paths(settings)
    return settings


def load_enviro(filename):
    '''
    Load the environment json file, loading additionaly imported
    environment files and massaging environment paths in the
    process.

    :type filename: string
    :param filename: filename of environment file to read

    :rtype: dictionary
    :return: dictionary representation of environment
    '''
    try:
        enviro = json.load(open(filename))
    except Exception:
        print 'Error reading environment file %s' % filename
        raise
    massage_enviro_paths(enviro)

    for key in enviro:
        if 'imports' in enviro[key]:
            for imp_file in enviro[key]['imports']:
                imp_enviro = load_enviro(imp_file)
                for imp_key in imp_enviro:
                    enviro[key][imp_key] = imp_enviro[imp_key]
            del enviro[key]['imports']

    return enviro


class InvalidTarget(Exception):
    '''
    An InvalidTarget exception is raised for exceptional conditions
    encountered while generating target lists.
    '''
    pass


def generate_target_list(enviro, args):
    '''
    Get a list of computers to run against from the command-line
    arguments.  Translate group names into lists of computers.

    :type enviro: dictionary
    :param enviro: environment to read group lists from
    :type args: args object
    :param args: object containing attributes for all possible command-line parameters

    :rtype: list of strings
    :return: list of computer names to run against
    '''
    host_list = []
    for target in args.target:
        if target in enviro['computers']:
            host_list.append(target)
        elif target in enviro['groups']:
            host_list.extend(enviro['groups'][target]['computers'])
        else:
            raise InvalidTarget("Invalid target '%s' encountered" % target)
            sys.exit(2)
    return host_list


def generate_run_list(enviro, args):
    '''
    Get the lists of computers, recipes, cookbooks, and run list to run
    against.  A run list is a dictionary containing a list of recipes
    and cookbooks to run against each specified computer.  Typically the
    run list will just specify the same recipes and cookbooks for each
    computer, unless a list of computers was given and the apply (-a)
    command-line argument was specified.  In that case each computer
    could have different things run against them.

    :type enviro: dictionary
    :param enviro: environment to read group lists and computer components from
    :type args: args object
    :param args: object containing attributes for all possible command-line parameters

    :rtype: tuple of (dictionary, list, list, list)
    :return: (run list, host list, recipe list, cookbook list)
    '''
    host_list = generate_target_list(enviro, args)
    run_list = {}
    cookbooks = set()
    recipes = set()
    if args.apply:
        for host in host_list:
            run_list[host] = []
            for comp in enviro['computers'][host]["components"]:
                if comp["type"] == 'cookbook':
                    run_list[host].append(comp)
                    cookbooks.add(comp["name"])
                elif comp["type"] == 'recipe':
                    run_list[host].append(comp)
                    recipes.add(comp["name"])
    else:
        for host in host_list:
            run_list[host] = []
            if args.cookbooks:
                run_list[host].extend([{"type": "cookbook", "name": c} for c in args.cookbooks])
            if args.recipes:
                run_list[host].extend([{"type": "recipe", "name": r} for r in args.recipes])
        if args.cookbooks:
            cookbooks.update(args.cookbooks)
        if args.recipes:
            recipes.update(args.recipes)
    return run_list, host_list, recipes, cookbooks


def output_pre_apply_messages(recipe_list, cookbook_list, enviro, settings, args):
    '''
    Ouptput all the pre-apply messages for the specified recipes and
    cookbooks.

    :type recipe_list: list
    :param recipe_list: list of recipes to process
    :type cookbook_list: list
    :param cookbook_list: list of cookbooks to process
    :type enviro: dictionary
    :param enviro: environment dictionary
    :type settings: dictionary
    :param settings: settings dictionary
    :type args: args object
    :param args: object containing attributes for all possible command-line parameters
    '''
    for r in recipe_list:
        recipe = recipes.recipes[r](
            settings, enviro, args.ok_to_be_rude, args.no_prompt)
        recipe.handle_pre_apply_message()

    for c in cookbook_list:
        cookbook = cookbooks.cookbooks[c](
            settings, enviro, args.ok_to_be_rude, args.no_prompt)
        cookbook.handle_pre_apply_messages()


def output_post_apply_messages(recipe_list, cookbook_list, enviro, settings, args):
    '''
    Ouptput all the post-apply messages for the specified recipes and
    cookbooks.

    :type recipe_list: list
    :param recipe_list: list of recipes to process
    :type cookbook_list: list
    :param cookbook_list: list of cookbooks to process
    :type enviro: dictionary
    :param enviro: environment dictionary
    :type settings: dictionary
    :param settings: settings dictionary
    :type args: args object
    :param args: object containing attributes for all possible command-line parameters
    '''
    for r in recipe_list:
        recipe = recipes.recipes[r](
            settings, enviro, args.ok_to_be_rude, args.no_prompt)
        recipe.handle_post_apply_message()

    for c in cookbook_list:
        cookbook = cookbooks.cookbooks[c](
            settings, enviro, args.ok_to_be_rude, args.no_prompt)
        cookbook.handle_post_apply_messages()


def apply_recipes_cookbooks(enviro, settings, args, host_list, run_list):
    '''
    Apply all specified recipes and cookbooks to the requested hosts.

    :type enviro: dictionary
    :param enviro: environment dictionary
    :type settings: dictionary
    :param settings: settings dictionary
    :type args: args object
    :param args: object containing attributes for all possible command-line parameters
    :type host_list: list of strings
    :param host_list: list of hosts to run against
    :type run_list: dictionary
    :param run_list: dictionary of lists
    '''
    for host in host_list:
        env.host_string = host
        if args.user:
            env.user = args.user

        if args.package_update:
            cuisine.package_update()

        try:
            for item in run_list[host]:
                if item["type"] == "recipe":
                    recipe = recipes.recipes[item["name"]](
                        settings, enviro, args.ok_to_be_rude, args.no_prompt)
                    recipe.run_apply(host)
                elif item["type"] == "cookbook":
                    cookbook = cookbooks.cookbooks[item["name"]](
                        settings, enviro, args.ok_to_be_rude, args.no_prompt)
                    cookbook.run_apply(host)
        finally:
            disconnect_all()


def main():
    '''
    Main function for the frycooker program.
    '''
    args = get_args()

    settings = load_settings(args.settings)
    enviro = load_enviro(args.environment)

    try:
        run_list, host_list, recipes, cookbooks = generate_run_list(enviro, args)

        if args.dryrun:
            print ("actions would be applied to the following hosts: %s" %
                   ', '.join(host_list))
            print ("environment to be used: %s" %
                   json.dumps(enviro, sort_keys=True, indent=4,
                              separators=(',', ': ')))
            sys.exit(0)

        output_pre_apply_messages(recipes, cookbooks, enviro, settings, args)
        if not args.messages:
            apply_recipes_cookbooks(enviro, settings, args, host_list, run_list)
        output_post_apply_messages(recipes, cookbooks, enviro, settings, args)

        print "actions completed successfully"
    except Exception, e:
        print "EXITING EARLY DUE TO AN EXCEPTION:"
        print e
        sys.exit(2)


if __name__ == "__main__":
    main()
