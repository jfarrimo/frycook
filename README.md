# Frycook

Frycook is a quick and dirty alternative to Chef.  When a giant kitchen full of equipment and a full staff headed by a master chef are *WAY* more than you need, a frycook will do the trick nicely.  It'as also nice when you'd rather do things in Python than having to learn Ruby or some other proprietary DSL.

Frycook is a thin layer on top of fabric, cuisine, and mako.  Frycook consists of the frycook package you install via pip, and a set of recipes and metadata files you generate to describe your environment and how to build it.  I'll call this set of recipes and metadata a _globule_ in this document.  There is a sample globule in the sample directory that handles a base server setup and web domain setup for a simple web server, based on Ubuntu 12.04.

The ideas embodied in frycook originally came from managing several hundred servers for a social gaming company, and then were augmented by time spent poring over the chef documentation.

The best way to learn frycook is to look through the code in the frycook module and in the sample that's included with this repo.

# environment.json

Here you keep all the metadata about the users, computers, and groups for your installation.

# recipes

A recipe describes how to install an individual package, such as postfix or nginx.  Frycook expects all your recipes to be in a module/package called 'recipes' that is accessible via the PYTHONPATH environment variable.  This module should export a list of recipe name and class tuples for use by the frycooker program.

# cookbooks

A cookbook is just a list of recipes to install.  You can add other logic to it, but basically it's just a list of recipes.  You need to put all your cookbooks in a module/package called 'cookbooks' that's in the PYTHONPATH environment variable.

# packages directory

This directory keeps copies of all the files for each recipe.  One of the major things a recipe does is copy config files to the server, and here's where they live, one directory per package.  Plain files are copied verbatim, while files with a .tmplt extension are treated as mako templates and processed before being copied to the server.

# frycooker

This is the job runner.  It takes as arguments a recipe or cookbook to run and a list of computers and groups to push the packages to.  Groups are expanded to computers and the contents are pushed to each one.

# settings.json

There are a few configuration settings for frycook, and they're set here.
