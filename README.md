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

TODO

# Examples

TODO
