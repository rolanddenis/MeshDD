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


def get_inside_faces_mask(mesh_faces, vertices_mask, border=False):
    """
    Returns mask of faces that are inside a given mask.

    Optionaly include border faces.
    """

    if border:
        return np.any(vertices_mask[mesh_faces], axis=1)
    else:
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


def get_boolean_difference(verticesA, verticesB, faces, vertices_mask=None, rtol=1e-5, atol=1e-8):
    """
    Boolean difference of a mesh and a displacement of the same mesh.

    Optional mask of vertices on which the two meshes differ.
    """

    # TODO: using ids (from nonzero) instead of mask is maybe faster (if needed)

    # Difference mask
    if vertices_mask is None:
        vertices_mask = np.logical_not(np.all(np.isclose(verticesA, verticesB, rtol, atol), axis=1))
    vertices_cnt = vertices_mask.sum()

    # Faces
    faces_mask = get_inside_faces_mask(faces, vertices_mask, border=True)
    faces_cnt = faces_mask.sum()

    # Border faces
    border_faces_mask = get_border_faces_mask(faces, vertices_mask)
    border_faces_cnt = border_faces_mask.sum()

    # Outside border vertices
    outside_border_vertices_mask = get_border_vertices_mask(faces, vertices_mask, border_faces_mask, outside=True)
    outside_border_vertices_cnt = outside_border_vertices_mask.sum()

    # Allocate vertices and faces of the resulting mesh
    diff_vertices = np.empty((outside_border_vertices_cnt + 2*vertices_cnt, verticesA.shape[1]), verticesA.dtype)
    diff_faces = np.empty((2 * faces_cnt, faces.shape[1]), faces.dtype)

    # Initialiazing vertices id map
    vertices_id_map = np.arange(verticesA.shape[0]) # TODO: reduced length depending on maximum of vertices id

    # Renumbering vertices of the outside border
    #outside_border_vertices_id = np.flatnonzero(outside_border_vertices_mask)
    vertices_id_map[outside_border_vertices_mask] = np.arange(outside_border_vertices_cnt)
    diff_vertices[:outside_border_vertices_cnt] = verticesA[outside_border_vertices_mask, :]

    # Inserting front faces
    vertices_id_map[vertices_mask] = outside_border_vertices_cnt + np.arange(vertices_cnt)
    diff_vertices[outside_border_vertices_cnt:(outside_border_vertices_cnt + vertices_cnt)] = verticesA[vertices_mask]
    diff_faces[:faces_cnt] = vertices_id_map[faces[faces_mask, :]]

    # Inserting back faces with flipped triangles
    vertices_id_map[vertices_mask] = outside_border_vertices_cnt + vertices_cnt + np.arange(vertices_cnt)
    diff_vertices[-vertices_cnt:] = verticesB[vertices_mask]
    diff_faces[-faces_cnt:] = vertices_id_map[faces[faces_mask, ::-1]]

    return diff_vertices, diff_faces


class MeshIOInterface:
    """ Mesh reader/writer interface for meshio """

    def read(self, mesh_file):
        assert mesh_file[-4:] == '.ply', "Only PLY format for input mesh"

        # Read mesh
        import meshio
        mesh = meshio.read(mesh_file)

        # Check that it is triangulated
        assert len(mesh.cells) == 1 and mesh.cells[0].type == 'triangle', "Mesh must be triangulated!"

        # Extract normals
        if all(k in mesh.point_data for k in ('nx', 'ny', 'nz')):
            normals = np.hstack((mesh.point_data['nx'][:, None],
                                 mesh.point_data['ny'][:, None],
                                 mesh.point_data['nz'][:, None]))
        else:
            normals = None

        # Extract texture coordinates
        if all(k in mesh.point_data for k in ('s', 't')):
            tcoords = np.hstack((mesh.point_data['s'][:, None],
                                 mesh.point_data['t'][:, None]))
        else:
            tcoords = None

        return mesh.points, mesh.cells[0].data, normals, tcoords

    def write(self, mesh_file, vertices, faces):
        import meshio
        meshio.write_points_cells(mesh_file, vertices, [("triangle", faces)])


class PyMeshInterface:
    """ Mesh reader/writer interface for pymesh """

    def read(self, mesh_file):
        assert mesh_file[-4:] == '.ply', "Only PLY format for input mesh"

        # Read mesh
        import pymesh
        mesh = pymesh.load_mesh(mesh_file)

        # Check that it is triangulated
        assert mesh.faces.shape[1] == 3, "Mesh must be triangulated!"

        # Extract normals
        if all(k in mesh.get_attribute_names() for k in ('vertex_nx', 'vertex_ny', 'vertex_nz')):
            normals = np.hstack((mesh.get_attribute('vertex_nx')[:, None],
                                 mesh.get_attribute('vertex_ny')[:, None],
                                 mesh.get_attribute('vertex_nz')[:, None]))
        else:
            normals = None

        # Extract texture coordinates
        if all(k in mesh.get_attribute_names() for k in ('vertex_s', 'vertex_t')):
            tcoords = np.hstack((mesh.get_attribute('vertex_s')[:, None],
                                 mesh.get_attribute('vertex_t')[:, None]))
        else:
            tcoords = None

        return mesh.vertices, mesh.faces, normals, tcoords

    def write(self, mesh_file, vertices, faces):
        import pymesh
        pymesh.save_mesh_raw(mesh_file, vertices, faces)



displace_length = 1e-2

# Command-line parameters
import sys
if len(sys.argv) < 3:
    print(f"Usage: {sys.argv[0]} <mesh> <texture>", file=sys.stderr)
    sys.exit(1)

mesh_file, texture_file = sys.argv[1:3]

# Mesh IO interface
#mesh_io_interface = MeshIOInterface()
mesh_io_interface = PyMeshInterface()

# Reading mesh
print("Reading mesh... ", end='', flush=True)
mesh_vertices, mesh_faces, mesh_normals, mesh_tcoords = mesh_io_interface.read(mesh_file)
print("Done.")

# Checking mesh
print("Checking mesh... ", end='', flush=True)
if mesh_tcoords is None:
    print("Missing texture coordinates (UV)!", file=sys.stderr)
    sys.exit(2)

if mesh_normals is None:
    print("Missing normals!", file=sys.stderr)
    sys.exit(2)

print("OK.")

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
#displace_mask = get_border_vertices_mask(mesh_faces, displace_mask, outside=True)
mesh_vertices_displaced = mesh_vertices.copy()
mesh_vertices_displaced[displace_mask, :] -= displace_length * mesh_normals[displace_mask, :]
print("Done.")

# Difference mesh
print("Difference mesh... ", end='', flush=True)
vertices_diff, faces_diff = get_boolean_difference(mesh_vertices, mesh_vertices_displaced, mesh_faces, displace_mask)
#vertices_diff, faces_diff = get_boolean_difference(mesh_vertices, mesh_vertices_displaced, mesh_faces)
print("Done.")

# Writing resulting mesh
print("Writing displaced mesh... ", end='', flush=True)
mesh_io_interface.write("testA.stl", mesh_vertices_displaced, mesh_faces)
print("Done.")

print("Writing difference mesh... ", end='', flush=True)
mesh_io_interface.write("testB.stl", vertices_diff, faces_diff)
print("Done.")

