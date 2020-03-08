# About MeshDD

MeshDD (for Mesh Displace & Difference) is a Python library meant to easily
split a mesh in multiples parts for multicolored 3D prints.

This is done through three main features:

- texture mapping on a mesh using given UV coordinates,
- vertices displacement along directions (e.g. normals) based on a given predicate (e.g. from texture threshold),
- boolean difference of two displaced meshes. 

The typical output is (for a bicolor print):

- a displaced version of the original mesh (e.g. the earth with carved seas)
- the difference mesh with respect to the original mesh (e.g. the seas)

This boolean difference algorithm works for meshes that differ from their
vertices positions only that allows it to be faster and more robust than
generic algorithms.

`tools` extra package also features a shape generator (currently only an
uv sphere), a generic (but basic) interface for reading, writing and cleaning a mesh using
[meshio](https://github.com/nschloe/meshio),
[PyMesh](https://github.com/PyMesh/PyMesh) or
[trimesh](https://github.com/mikedh/trimesh),
and some examples packaged as command-line scripts.

# Known limitations

- works only with triangulated meshes,
- meshes must differ from their vertices positions only,
- doesn't handle mesh auto-intersection during displacement,
- optional mesh reader accepts only PLY format (to have normals and texture coordinates per vertex).

# Requirements

The core features require `numpy` only.
To use all features from the `tools` extra package, you will additionaly need:

- `imageio` to read a texture from an image,
- `meshio` (no additional dependencies), `pymesh2` or `trimesh` (faster) to read and write meshes,
- `scipy` for the `meshdd_tricolor_earth` script that split the Earth in land, sea and ice.

# Installation

Simply clone this project and install it using `pip`:
```bash
git clone https://github.com/rolanddenis/MeshDD.git
pip install MeshDD
```

Use `pip install MeshDD[tools]` instead if you want to install the optional dependencies needed by the `tools` extra package.

MeshDD can also be used without installation by simply picking the `src/meshdd.py` file only.

# Quick Start

Here is an example of creating a bicolor ladybird-like torus:

```python
import numpy as np
import meshdd
import meshdd.tools

# Creating a torus with 1001x1001 vertices, major radius of 50 and minor radius of 25
vertices, faces, normals, tcoords = meshdd.tools.create_torus(1001, 1001, 50, 25)

# Creating the mask for 10x5 circle-like inclusions
displace_mask = np.square(np.mod(tcoords * [10, 5], 1.) - 0.5).sum(axis=1) <= 0.25**2

# Displacing the original vertices depending on the mask
displaced_vertices = meshdd.displace_vertices(vertices, normals, -10, displace_mask)

# Calculating the boolean difference between the original mesh and the displaced one
diff_vertices, diff_faces = meshdd.get_boolean_difference(vertices, displaced_vertices, faces, displace_mask)

# Saving the two meshes using trimesh
mesh_interface = meshdd.tools.TriMeshInterface()
mesh_interface.write('torus_displaced.stl', displaced_vertices, faces)
mesh_interface.write('torus_difference.stl', diff_vertices, diff_faces)
```

Load the two resulting meshes in you favourite slicer and you will be able to print it using two filaments.

# Examples

TODO
