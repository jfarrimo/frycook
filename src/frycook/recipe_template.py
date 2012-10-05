import os
import os.path
import re

import cuisine
from mako.lookup import TemplateLookup

class RecipeException(Exception):
    pass

class Recipe(object):
    def __init__(self, settings, environment):
        self.settings = settings
        self.environment = environment
        self.mylookup = TemplateLookup(
            directories=[self.settings["package_dir"]], 
            module_directory=self.settings["module_dir"])

    def pre_apply_checks(self, computer):
        # make sure the computer is in our enviro
        if computer not in self.environment["computers"]:
            raise RecipeException(
                "computer %s not defined in environment" % computer)

    def apply(self, computer):
        pass

    def post_apply_cleanup(self, computer):
        pass

    def cleanup(self, computer):
        pass

    def run_apply(self, computer):
        self.pre_apply_checks(computer)
        self.apply(computer)
        self.post_apply_cleanup(computer)

    def run_cleanup(self, computer):
        self.cleanup(computer)

    def push_file(self, local_name, remote_name):
        cuisine.file_upload(remote_name, 
                            os.path.join(self.settings["package_dir"], 
                                         local_name))

    def push_template(self, templatename, out_path, enviro):
        mytemplate = self.mylookup.get_template(templatename)
        buff = mytemplate.render(**enviro)
        cuisine.file_write(out_path, buff, check=True)

    def push_package_file_set(self, package_name, template_env):
        work_dir = os.path.join(self.settings["package_dir"], 
                                package_name)
        os.chdir(work_dir)
        for root, dirs, files in os.walk('.'):
            for f in files:
                filename = os.path.join(root, f).lstrip('./')
                if re.search(self.settings["file_ignores"], filename) is None:
                    base_path, ext = os.path.splitext(filename)
                    if ext == '.tmplt':
                        self.push_template(os.path.join(package_name, filename),
                                           os.path.join('/', base_path),
                                           template_env)
                    else:
                        self.push_file(os.path.join(work_dir, filename),
                                       os.path.join('/', filename))
