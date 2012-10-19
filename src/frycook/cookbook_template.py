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
Cookbooks are sets of recipes to apply to a server
to create something that is made up of many packages.
'''

class Cookbook(object):
    '''
    Base object for all cookbooks to be created from.  Subclass
    this for your own cookbooks.  Generally you'll just define
    a list of recipes to run in recipe_list.  If you over-ride
    any of the functions, be sure to call the base class
    functions so that all the good stuff still happens.

    In your overridden class you'll fill recipe_list with class
    objects for recipes that you want run when applying the
    cookbook.  It's best to define this at the class level.
    The recipes will be applied in the order they're defined
    in the list.

    example::

      recipe_list = [AwesomeRecipe, WayCoolRecipe]
    '''
    recipe_list = []

    def __init__(self, settings, environment):
        '''
        @type settings: dict
        @param settings: settings dictionary
        @type environment: dict
        @param environment: metadata dictionary
        '''
        self.recipes = []
        for recipe in self.recipe_list:
            self.recipes.append(recipe(settings, environment))

    #######################
    ######## APPLY ########
    #######################

    def pre_apply_checks(self, computer):
        '''
        Runs the pre_apply_checks functions for all the recipes
        defined in recipe_list. Override this if there's 
        something you need to check above and beyond the 
        recipe-level data.  Be sure to call the base if you
        subclass this.

        @type computer: string
        @param computer: computer to apply recipe checks to
        '''
        for recipe in self.recipes:
            recipe.pre_apply_checks(computer)

    def apply(self, computer):
        '''
        Runs the apply functions for all the recipes defined
        in recipe_list.  Override this if there's something you
        need to do besides just running all the recipes.  Be
        sure to call the base class if you subclass this.

        @type computer: string
        @param computer: computer to apply recipe to
        '''
        for recipe in self.recipes:
            recipe.apply(computer)

    def run_apply(self, computer):
        '''
        Run the apply process for the computer.  This is usually
        just called from frycooker.

        @type computer: string
        @param computer: computer to apply recipe to
        '''
        self.pre_apply_checks(computer)
        self.apply(computer)

    #########################
    ######## CLEANUP ########
    #########################

    def run_cleanup(self, computer):
        '''
        Run the cleanup process for the computer.  This is usually
        just called from frycooker.

        @type computer: string
        @param computer: computer to apply recipe cleanup to
        '''
        for recipe in self.recipes:
            recipe.run_cleanup(computer)
