import cuisine

from frycook import Recipe, RecipeException


class RecipeExampleCom(Recipe):
    def __init__(self, settings, environment):
        super(RecipeExampleCom, self).__init__(settings, environment)
        self.username = 'example_com'

    def pre_apply_checks(self, computer):
        super(RecipeExampleCom, self).pre_apply_checks(computer)

        # make sure the example_com user is in our enviro
        if self.username not in self.environment["users"]:
            raise RecipeException(
                "%s user not defined in environment" % self.username)

    def apply(self, computer):
        username = "example_com"
        if not cuisine.user_check(username):
            cuisine.user_create(username)
            cuisine.sudo('usermod -p `openssl rand -base64 32` %s' % username)

        key = self.environment["users"][username]["ssh_public_key"]
        cuisine.ssh_authorize(username, key)

        cuisine.dir_ensure('/home/example_com/www', mode='755',
                           owner=username, group=username)
        cuisine.file_link('/home/example_com/www',
                          '/srv/www/example_com')

        self.push_package_file_set('example_com', computer)

        cuisine.file_link('/etc/nginx/sites-available/example_com',
                          '/etc/nginx/sites-enabled/example_com')

        cuisine.sudo("service nginx restart")
