import cuisine

from frycook import Recipe

class RecipeSSH(Recipe):
    def apply(self, computer):
        # the ssh package is already installed, or else we woudln't
        # be able to run all the fabric/cuisine stuff

        tmp_env = {"computer": self.environment['computers'][computer]}
        self.push_package_file_set('ssh', tmp_env)

        cuisine.sudo("service ssh restart")
