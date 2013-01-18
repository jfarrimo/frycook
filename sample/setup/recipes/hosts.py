import cuisine

from frycook import Recipe

class RecipeHosts(Recipe):
    def apply(self, computer):
        group = self.environment["computers"][computer]["host_group"]
        computers = self.environment["groups"][group]["computers"]
        sibs = [comp for comp in computers if comp != computer]
        tmp_env = {"host": computer,
                   "sibs": sibs,
                   "computers": self.environment["computers"]}
        self.push_package_file_set('hosts', computer, tmp_env)

        cuisine.sudo("service hostname restart")
