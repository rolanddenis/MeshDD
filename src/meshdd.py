import numpy as np

def get_texture_from_image(image):
    """ Transform an image into a texture"""

    # Image axis order is reversed and origin is in the up-left corner.
    return np.swapaxes(image, 0, 1)[:, ::-1, ...]

def displace_vertices(vertices, directions, length=1., mask=True):
    """ Displace vertices by given length along directions where mask is True """
    # Multiplicating length by mask beforehand to allow broadcasting
    return vertices + np.atleast_1d(length * mask)[:, None] * normals

def get_vertex_color_from_texture(tcoords, texture):
    """ From a texture and the texture coords of a mesh, returns the color per vertex """
    tcoords_scaled = np.minimum(
        np.array(texture.shape) - 1,
        np.maximum((0, 0),
                   np.floor(tcoords * texture.shape).astype(np.int64)))

    return texture[tcoords_scaled[:, 0], tcoords_scaled[:, 1], ...]


def get_border_faces_mask(faces, vertices_mask):
    """ Returns mask of faces that are on the the bounds of a given mask """

    # Per face, count vertices that are inside the mask
    inside_vertices_count = vertices_mask[faces].sum(axis=1)

    # Get faces that cross the border (0 < count < vertices per faces)
    return (0 < inside_vertices_count) & (inside_vertices_count < faces.shape[1])


def get_inside_faces_mask(faces, vertices_mask, border=False):
    """
    Returns mask of faces that are inside a given mask.

    Optionaly includes border faces.
    """

    if border:
        return np.any(vertices_mask[faces], axis=1)
    else:
        return np.all(vertices_mask[faces], axis=1)


def get_border_vertices_mask(faces, vertices_mask, border_faces_mask=None, outside=False):
    """
    Returns mask of vertices that are on the inside (or outside) bounds of a given mask

    Optional mask of border faces calculated from get_border_faces_maks.
    Set outside to True to return the mask of the outside bounds.
    """

    # Mask of faces that lie on the border
    if border_faces_mask is None:
        border_faces_mask = get_border_faces_mask(faces, vertices_mask)
    border_faces = faces[border_faces_mask, :]

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
    # TODO: reduced length depending on maximum of vertices id
    vertices_id_map = np.arange(verticesA.shape[0])

    # Renumbering vertices of the outside border
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


