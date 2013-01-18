from frycook import Cookbook

from recipes import RecipeHosts
from recipes import RecipeRootUser
from recipes import RecipeShorewall
from recipes import RecipeSSH
from recipes import RecipeFail2ban
from recipes import RecipePostfix

class CookbookBase(Cookbook):
    recipe_list = [RecipeRootUser,
                   RecipeHosts,
                   RecipeShorewall,
                   RecipeSSH,
                   RecipeFail2ban,
                   RecipePostfix]
# nagios-client,emacs
