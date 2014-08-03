import cuisine

from frycook import Recipe


class RecipeSSH(Recipe):
    def apply(self, computer):
        # the ssh package is already installed, or else we woudln't
        # be able to run all the fabric/cuisine stuff
        self.push_package_file_set('ssh', computer)

        cuisine.sudo("service ssh restart")
