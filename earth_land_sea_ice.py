#!/usr/bin/env python3

import draft
import shapes
import imageio
import argparse
import numpy as np
import os
from scipy.ndimage.filters import gaussian_filter

# Command-line parameters
parser = argparse.ArgumentParser(
    description="Create an earth mesh with three colors for land, sea and ice",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("texture", type=str, nargs=1,
                    help="Earth image from https://visibleearth.nasa.gov/images/57730")
parser.add_argument("--Ntheta", type=int, default=501,
                    help="Number of discretization points for the longitude")
parser.add_argument("--Nphi", type=int, default=501,
                    help="Number of discretization points for the latitude")
parser.add_argument("--radius", type=float, default=50,
                    help="Sphere radius")
parser.add_argument("--depth", type=float, default=1.2,
                    help="Displaciement depth")
parser.add_argument("--sigma", type=float, default=1,
                    help="Standard deviation used to define the Gaussian blur kernel when splitting texture") 
parser.add_argument("--output", type=str, default="earth.stl",
                    help="Output file name")
options = parser.parse_args()

# Creating sphere mesh
print("Creating sphere mesh...", end='', flush=True)
vertices, faces, normals, tcoords = shapes.create_sphere(options.Ntheta, options.Nphi)
vertices *= options.radius
print("Done.")

# Reading texture image
print("Reading texture...", end='', flush=True)
texture = draft.get_texture_from_image(imageio.imread(options.texture[0])).astype(float)
print("Done.")

# Calculating land, sea and ice maks
print("Calculating land, sea and ice mask...", end='', flush=True)
ice_mask = np.logical_and(texture.mean(axis=2) >= 200, texture[:, :, -1] >= np.max(texture[:, :, :2], axis=2))
sea_mask = texture[:, :, -1] >= 1.5*np.max(texture[:, :, :1], axis=2)
land_mask = np.logical_not(np.logical_or(ice_mask, sea_mask))
land_mask = gaussian_filter(land_mask.astype(float), sigma=options.sigma) >= 0.5
ice_mask = gaussian_filter(ice_mask.astype(float), sigma=options.sigma) >= 0.5
sea_mask = np.logical_not(np.logical_or(land_mask, ice_mask))
print("Done.")

# Displace and difference for the sea
print("Displacing and difference for the sea part...", end='', flush=True)
displace_mask = draft.get_vertex_color_from_texture(tcoords, sea_mask)
tmp_vertices = draft.displace_vertices(vertices, normals, -options.depth, displace_mask)
sea_vertices, sea_faces = draft.get_boolean_difference(vertices, tmp_vertices, faces, displace_mask)
print("Done.")

# Displace and difference for the ice
print("Displacing and difference for the ice part...", end='', flush=True)
displace_mask = draft.get_vertex_color_from_texture(tcoords, ice_mask)
land_vertices = draft.displace_vertices(tmp_vertices, normals, -options.depth, displace_mask)
ice_vertices, ice_faces = draft.get_boolean_difference(tmp_vertices, land_vertices, faces, displace_mask)
print("Done.")

# Writing resulting mesh
filename_prefix, filename_extension = os.path.splitext(options.output)
#mesh_io_interface = draft.MeshIOInterface()
mesh_io_interface = draft.PyMeshInterface()

print("Writing land mesh... ", end='', flush=True)
mesh_io_interface.write(filename_prefix + "_land" + filename_extension, land_vertices, faces)
print("Done.")

print("Writing sea mesh... ", end='', flush=True)
mesh_io_interface.write(filename_prefix + "_sea" + filename_extension, sea_vertices, sea_faces)
print("Done.")

print("Writing ice mesh... ", end='', flush=True)
mesh_io_interface.write(filename_prefix + "_ice" + filename_extension, ice_vertices, ice_faces)
print("Done.")
