from fail2ban import RecipeFail2ban
from hosts import RecipeHosts
from nginx import RecipeNginx
from postfix import RecipePostfix
from root_user import RecipeRootUser
from example_com import RecipeExampleCom
from shorewall import RecipeShorewall
from ssh import RecipeSSH

recipes = {
    'fail2ban': RecipeFail2ban,
    'hosts': RecipeHosts,
    'nginx': RecipeNginx,
    'postfix': RecipePostfix,
    'root_user': RecipeRootUser,
    'example_com': RecipeExacmpleCom,
    'shorewall': RecipeShorewall,
    'ssh': RecipeSSH
    }
