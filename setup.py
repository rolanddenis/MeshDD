#!/usr/bin/env python

from distutils.core import setup

setup(name='meshdd',
      version='0.1',
      description='Displace a mesh and extract boolean difference for multi-colors 3D printing',
      author='Roland Denis',
      author_email='denis@math.univ-lyon1.fr',
      packages=['meshdd', 'meshdd.tools'],
      packages_dir={'meshdd': 'src'},
      requires=['numpy'],
      extra_requires={'tools': ['imageio', 'scipy', 'meshio', 'pymesh2', 'trimesh']},
      entry_points={
          'console_scripts': ['meshdd_sphere_two_colors=meshdd.tools.sphere_two_colors']
      },
)
                    
