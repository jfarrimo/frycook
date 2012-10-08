from frycook import Cookbook

from recipes import RecipeNginx
from recipes import RecipeExampleCom

class CookbookWeb(Cookbook):
    recipe_list = [RecipeNginx, 
                   RecipeExampleCom]
