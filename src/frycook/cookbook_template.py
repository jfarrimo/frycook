class Cookbook(object):
    recipe_list = []

    def __init__(self, settings, environment):
        self.recipes = []
        for recipe in self.recipe_list:
            self.recipes.append(recipe(settings, environment))

    def pre_apply_checks(self, computer):
        for recipe in self.recipes:
            recipe.pre_apply_checks(computer)

    def apply(self, computer):
        for recipe in self.recipes:
            recipe.apply(computer)

    def post_apply_cleanup(self, computer):
        for recipe in self.recipes:
            recipe.post_apply_cleanup(computer)

    def run_cleanup(self, computer):
        for recipe in self.recipes:
            recipe.run_cleanup(computer)

    def run_apply(self, computer):
        self.pre_apply_checks(computer)
        self.apply(computer)
        self.post_apply_cleanup(computer)

    def run_cleanup(self, computer):
        self.cleanup(computer)
