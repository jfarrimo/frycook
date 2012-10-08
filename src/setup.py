from distutils.core import setup

setup(name='frycook',
      version='0.1.3',
      description='frycook system builder',
      author='Jay Farrimond',
      author_email='jay@farrimond.com',
      url='http://github.com/jfarrimo/frycook',
      packages=['frycook'],
      scripts=['frycooker'],
      install_requires=['fabric', 'cuisine', 'mako'],
      )
