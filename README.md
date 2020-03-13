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
- optional mesh reader accepts PLY format only (to have normals and texture coordinates per vertex) but you can use any other format using another mesh library (e.g. [trimesh](https://github.com/mikedh/trimesh)),
- doesn't adapt or subdivise the mesh to best fit the displacement.

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

<p align="center"><img src="doc/images/ladybird_torus.jpg?raw=true" alt="Ladybird-like torus" height="400px"></p>

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

## Bicolor Earth (land/sea)

<p align="center"><img src="doc/images/bicolor_earth.jpg?raw=true" alt="Bicolor Earth" height="400px"></p>

Starting from a land/water mask image (e.g. the 8192x4096 PNG land/water mask from [Natural Earth III](http://www.shadedrelief.com/natural3/pages/extra.html), smoothed in GIMP using a Gaussian filter of 16px)
you can split a sphere in a sea and land part for bicolor 3D printing:

```python
import numpy as np
import meshdd
import meshdd.tools
import imageio

# Creating a sphere of radius 50 with 1001x1001 vertices 
vertices, faces, normals, tcoords = meshdd.tools.create_sphere(1001, 1001)
vertices *= 50

# Reading land/water mask and fixing image origin
texture = meshdd.get_texture_from_image(imageio.imread("water_8k.png"))

# Calculating color per vertex
vertex_color = meshdd.get_vertex_color_from_texture(tcoords, texture)

# Creating the corresponding mask (sea <=> True)
displace_mask = vertex_color >= 0.5

# Carving the sea
displaced_vertices = meshdd.displace_vertices(vertices, normals, -1.2, displace_mask)

# Calculating the sea mesh from the boolean difference with the original sphere
diff_vertices, diff_faces = meshdd.get_boolean_difference(vertices, displaced_vertices, faces, displace_mask)

# Saving the two meshes using trimesh
mesh_interface = meshdd.tools.TriMeshInterface()
mesh_interface.write('earth_land.stl', displaced_vertices, faces)
mesh_interface.write('earth_sea.stl', diff_vertices, diff_faces)
```

Take a look at the `src/tools/bicolor_sphere.py` example script, available as `meshdd_bicolor_sphere` after installation.

## Bicolor mesh (land/sea)

<p align="center">
  <img src="doc/images/hevea_bicolor_earth_IC1.jpg?raw=true" alt="Hevea Earth at first iteration" height="400px">
  <img src="doc/images/hevea_bicolor_earth_IC2.jpg?raw=true" alt="Hevea Earth at second iteration" height="400px">
</p>

Also note that the script `src/tools/bicolor_mesh.py` do the same but on a given mesh.
It simply uses the optional mesh reader interface to read a mesh (left image using a mesh from [Hevea project](http://hevea-project.fr/ENIndexHevea.html)):
```python
mesh_interface = meshdd.tools.TriMeshInterface()

# First iteration of shrinking a sphere using convex integration
vertices, faces, normals, tcoords = mesh_interface.read("hevea_sphere_IC1.ply")
```

You can also use another normal field (or calculate your own) to avoid self-intersections (right image):
```python
mesh_interface = meshdd.tools.TriMeshInterface()

# Second iteration of shrinking a sphere using convex integration
vertices, faces, normals, tcoords = mesh_interface.read("hevea_sphere_IC2.ply")

# Using smoother normals of first iteration to avoid self-intersections after displacement
_, _, normals, _ = mesh_interface.read("hevea_sphere_IC1.ply")
```

## Tricolor Earth (land/sea/ice)

<p align="center"><img src="doc/images/earth_land_sea_ice.jpg?raw=true" alt="Earth with land, sea and ice" height="400px"></p>

We can also chain displacements and differences to split a mesh in more than two parts,
for example to extract land, sea and ice parts from [The Blue Marble](https://visibleearth.nasa.gov/images/57730):

```python
import numpy as np
import meshdd
import meshdd.tools
import imageio

# Creating a sphere of radius 50 with 1001x1001 vertices 
vertices, faces, normals, tcoords = meshdd.tools.create_sphere(1001, 1001)
vertices *= 50

# Reading Earth texture
texture = meshdd.get_texture_from_image(imageio.imread("land_ocean_ice_2048.png"))

# A little elbow grease to separate land, sea and ice and smoothing everything
from scipy.ndimage.filters import gaussian_filter
ice_mask = np.logical_and(texture.mean(axis=2) >= 200, texture[:, :, -1] >= np.max(texture[:, :, :2], axis=2))
sea_mask = texture[:, :, -1] >= 1.5*np.max(texture[:, :, :1], axis=2)
land_mask = np.logical_not(np.logical_or(ice_mask, sea_mask))
land_mask = gaussian_filter(land_mask.astype(float), sigma=1) >= 0.5
ice_mask = gaussian_filter(ice_mask.astype(float), sigma=1) >= 0.5
sea_mask = np.logical_not(np.logical_or(land_mask, ice_mask))

# Displace and difference for the sea
displace_mask = meshdd.get_vertex_color_from_texture(tcoords, sea_mask)
land_tmp_vertices = meshdd.displace_vertices(vertices, normals, -1.2, displace_mask)
sea_vertices, sea_faces = meshdd.get_boolean_difference(vertices, land_tmp_vertices, faces, displace_mask)

# Displace and difference for the ice
displace_mask = meshdd.get_vertex_color_from_texture(tcoords, ice_mask)
land_vertices = meshdd.displace_vertices(land_tmp_vertices, normals, -1.2, displace_mask)
ice_vertices, ice_faces = meshdd.get_boolean_difference(land_tmp_vertices, land_vertices, faces, displace_mask)

# Saving the meshes using trimesh
mesh_interface = meshdd.tools.TriMeshInterface()
mesh_interface.write('earth_land.stl', land_vertices, faces)
mesh_interface.write('earth_sea.stl', sea_vertices, sea_faces)
mesh_interface.write('earth_ice.stl', ice_vertices, ice_faces)
```

Take a look at the `src/tools/tricolor_earth.py` example script, available as `meshdd_tricolor_earth` after installation.

## Earth with amplified topography and bathymetry

(e.g. to print the sea with a transparent filament)

**TODO**
