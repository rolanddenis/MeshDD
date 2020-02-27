#!/usr/bin/env python3

import numpy as np

def get_texture_from_file(texture_file):
    """ Read texture from an image """
    import imageio

    # Image axis order is reversed and origin is in the up-left corner.
    return imageio.imread(texture_file).T[:, ::-1]


def get_vertex_color_from_texture(mesh_tcoords, texture):
    """ From a texture and the texture coords of a mesh, returns the color per vertex """
    tcoords_scaled = np.minimum(
        np.array(texture.shape) - 1,
        np.maximum((0, 0), 
                   np.floor(mesh_tcoords * texture.shape).astype(np.int64)))

    return texture[tcoords_scaled[:, 0], tcoords_scaled[:, 1], ...]


def get_border_faces_mask(mesh_faces, vertices_mask):
    """ Returns mask of faces that are on the the bounds of a given mask """

    # Per face, count vertices that are inside the mask
    inside_vertices_count = vertices_mask[mesh_faces].sum(axis=1)

    # Get faces that cross the border (0 < count < vertices per faces)
    return (0 < inside_vertices_count) & (inside_vertices_count < mesh_faces.shape[1])


def get_inside_faces_mask(mesh_faces, vertices_mask):
    """ Returns mask of faces that are inside a given mask """
    return np.all(vertices_mask[mesh_faces], axis=1)


def get_border_vertices_mask(mesh_faces, vertices_mask, border_faces_mask=None, outside=False):
    """
    Returns mask of vertices that are on the inside (or outside) bounds of a given mask
    
    Optional mask of border faces calculated from get_border_faces_maks.
    Set outside to True to return the mask of the outside bounds.
    """
   
    # Mask of faces that lie on the border
    if border_faces_mask is None:
        border_faces_mask = get_border_faces_mask(mesh_faces, vertices_mask)
    border_faces = mesh_faces[border_faces_mask, :]

    # From these faces, get the (non-unique) id of their vertices that are inside the input mask
    if outside:
        border_vertices_id = border_faces[np.logical_not(vertices_mask[border_faces])]
    else:
        border_vertices_id = border_faces[vertices_mask[border_faces]]

    # Define the corresponding mask
    border_vertices_mask = np.full_like(vertices_mask, False)
    border_vertices_mask[border_vertices_id] = True

    return border_vertices_mask


def get_boolean_difference(meshA, meshB, vertices_mask):
    """
    Boolean difference of a mesh and a displacement of the same mesh.

    The two meshes should differ on for the vertices designated by
    the given mask.
    """

    pass 

displace_length = 1e-2

# Command-line parameters
import sys
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <mesh> <texture>", file=sys.stderr)
    sys.exit(1)

mesh_file, texture_file = sys.argv[1:3]

# Reading mesh
print("Reading mesh... ", end='', flush=True)
import meshio
mesh = meshio.read(mesh_file)
print("Done.")

# Checking mesh
print("Checking mesh... ", end='', flush=True)
if any(cb.type != 'triangle' for cb in mesh.cells):
    print("Works only on triangulated mesh!", file=sys.stderr)
    sys.exit(2)

if any(k not in mesh.point_data for k in ('s', 't')):
    print("Missing texture coordinates (UV)!", file=sys.stderr)
    sys.exit(2)

if any(k not in mesh.point_data for k in ('nx', 'ny', 'nz')):
    print("Missing normals!", file=sys.stderr)
    sys.exit(2)

print("OK.")

mesh_vertices = mesh.points
mesh_tcoords = np.hstack((mesh.point_data['s'][:, None], mesh.point_data['t'][:, None]))
mesh_normals = np.hstack((mesh.point_data['nx'][:, None], mesh.point_data['ny'][:, None], mesh.point_data['nz'][:, None]))
mesh_faces = mesh.cells[0].data

print(f"#vertex={mesh_vertices.shape[0]} #triangles={mesh_faces.shape[0]}")
print(f"Mesh bounds: min={np.amin(mesh_vertices, axis=0)} max={np.amax(mesh_vertices, axis=0)}")
print(f"UV bounds: min={np.amin(mesh_tcoords, axis=0)} max={np.amax(mesh_tcoords, axis=0)}")

# Reading texture
print("Reading texture... ", end='', flush=True)
texture = get_texture_from_file(texture_file)
print("Done.")

# Displacing mesh
print("Displacing mesh... ", end='', flush=True)
vertex_color = get_vertex_color_from_texture(mesh_tcoords, texture)
displace_mask = vertex_color == 255
displace_mask = get_border_vertices_mask(mesh_faces, displace_mask, outside=True)
mesh_vertices[displace_mask, :] -= displace_length * mesh_normals[displace_mask, :]
print("Done.")

# Writing resulting mesh
print("Writing mesh... ", end='', flush=True)
meshio.write("test.ply", mesh)
print("Done.")
