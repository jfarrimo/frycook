import cuisine
from fabric.context_managers import prefix

from frycook import Recipe

class RecipeNginx(Recipe):
    '''
    Let's serve all the files from the /srv/www directory
    instead of the default /usr/share/nginx/www.
    '''
    def apply(self, computer):
        cuisine.package_ensure('nginx-extras')

        cuisine.dir_ensure('/srv/www/', mode='755')

        tmp_env = {"name": computer}
        self.push_package_file_set('nginx', computer, tmp_env)

        cuisine.sudo("service nginx restart")
