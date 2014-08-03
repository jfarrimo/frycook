import cuisine
from fabric.context_managers import prefix

from frycook import Recipe


class RecipePostfix(Recipe):
    def apply(self, computer):
        with prefix('export DEBIAN_FRONTEND=noninteractive'):
            cuisine.package_ensure('postfix')
            cuisine.package_ensure('mailutils')

        tmp_env = {"name": computer}
        self.push_package_file_set('postfix', computer, tmp_env)

        cuisine.sudo("/usr/bin/newaliases")
        cuisine.sudo("service postfix restart")
