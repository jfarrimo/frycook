import cuisine

from frycook import Recipe


class RecipeFail2ban(Recipe):
    def apply(self, computer):
        cuisine.package_ensure('fail2ban')
