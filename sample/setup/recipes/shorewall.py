import cuisine

from frycook import Recipe

class RecipeShorewall(Recipe):
    def apply(self, computer):
        cuisine.package_ensure('shorewall')
        cuisine.package_ensure('shorewall-doc')

        tmp_env = {"computer": self.environment['computers'][computer]}
        self.push_package_file_set('shorewall', tmp_env)

        cuisine.sudo("service shorewall restart")
