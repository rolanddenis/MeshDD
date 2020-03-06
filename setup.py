#!/usr/bin/env python

from setuptools import setup

setup(name='MeshDD',
      version='0.1',
      description='Displace a mesh and extract boolean Difference for multi-colors 3D printing',
      author='Roland Denis',
      author_email='denis@math.univ-lyon1.fr',
      packages=['meshdd', 'meshdd.tools'],
      package_dir={'meshdd': 'src'},
      requires=['numpy'],
      extras_require={'tools': ['imageio', 'scipy', 'meshio', 'pymesh2', 'trimesh']},
      entry_points={
          'console_scripts': [
              'meshdd_bicolor_sphere = meshdd.tools.bicolor_sphere:main',
              'meshdd_tricolor_earth = meshdd.tools.tricolor_earth:main',
              'meshdd_bicolor_mesh = meshdd.tools.bicolor_mesh:main',
          ]
      },
)

