import cuisine

from frycook import Recipe


class RecipeShorewall(Recipe):
    def apply(self, computer):
        cuisine.package_ensure('shorewall')
        cuisine.package_ensure('shorewall-doc')

        self.push_package_file_set('shorewall', computer)

        cuisine.sudo("service shorewall restart")
