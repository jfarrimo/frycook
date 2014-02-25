import cuisine

from frycook import Recipe, RecipeException


class RecipeRootUser(Recipe):
    def pre_apply_checks(self, computer):
        super(RecipeRootUser, self).pre_apply_checks(computer)

        # make sure the root user is in our enviro
        if "root" not in self.environment["users"]:
            raise RecipeException("root user not defined in environment")

    def apply(self, computer):
        username = "root"
        cuisine.user_ensure(username)

        key = self.environment["users"][username]["ssh_public_key"]
        cuisine.ssh_authorize(username, key)
