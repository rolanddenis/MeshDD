#!/usr/bin/env python3

import draft
import shapes
import imageio
import argparse
import numpy as np
import os

# Command-line parameters
parser = argparse.ArgumentParser(
    description="Create a bicolor sphere from a texture",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("texture", type=str, nargs=1,
                    help="Image used to split the mesh in two color")
parser.add_argument("--Ntheta", type=int, default=501,
                    help="Number of discretization points for the longitude")
parser.add_argument("--Nphi", type=int, default=501,
                    help="Number of discretization points for the latitude")
parser.add_argument("--radius", type=float, default=50,
                    help="Sphere radius")
parser.add_argument("--threshold", type=float, default=128,
                    help="Threshold value from the image used to split the sphere."
                         "By default, vertices corresponding to values above the threshold are carved.")
parser.add_argument("--reverse", action="store_true",
                    help="Vertices below the threshold are carved.")
parser.add_argument("--depth", type=float, default=1.2,
                    help="Displacement depth")
parser.add_argument("--output", type=str, default="sphere.stl",
                    help="Output file name")
options = parser.parse_args()

# Creating sphere mesh
print("Creating sphere mesh...", end='', flush=True)
vertices, faces, normals, tcoords = shapes.create_sphere(options.Ntheta, options.Nphi)
vertices *= options.radius
print("Done.")

# Reading texture image
print("Reading texture...", end='', flush=True)
texture = draft.get_texture_from_image(imageio.imread(options.texture[0]))
print("Done.")

# Displacing mesh
print("Displacing mesh... ", end='', flush=True)
vertex_color = draft.get_vertex_color_from_texture(tcoords, texture)
if vertex_color.ndim > 1:
    vertex_color = np.mean(vertex_color, axis=1)

displace_mask = vertex_color >= options.threshold
if options.reverse:
    displace_mask = np.logical_not(displace_mask)

displaced_vertices = draft.displace_vertices(vertices, normals, -options.depth, displace_mask)
print("Done.")

# Difference mesh
print("Difference mesh... ", end='', flush=True)
diff_vertices, diff_faces = draft.get_boolean_difference(vertices, displaced_vertices, faces, displace_mask)
print("Done.")

# Writing resulting mesh
filename_prefix, filename_extension = os.path.splitext(options.output)
#mesh_io_interface = draft.MeshIOInterface()
mesh_io_interface = draft.PyMeshInterface()

print("Writing displaced mesh... ", end='', flush=True)
mesh_io_interface.write(filename_prefix + "_displaced" + filename_extension, displaced_vertices, faces)
print("Done.")

print("Writing difference mesh... ", end='', flush=True)
mesh_io_interface.write(filename_prefix + "_difference" + filename_extension, diff_vertices, diff_faces)
print("Done.")
