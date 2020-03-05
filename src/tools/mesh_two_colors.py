#!/usr/bin/env python3

def get_texture_from_file(texture_file):
    """ Read texture from an image """
    import imageio

    # Image axis order is reversed and origin is in the up-left corner.
    return imageio.imread(texture_file).T[:, ::-1]

if __name__ == "__main__":

    displace_length = 1e-2

    # Command-line parameters
    import sys
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <mesh> <texture>", file=sys.stderr)
        sys.exit(1)

    mesh_file, texture_file = sys.argv[1:3]

    # Mesh IO interface
    #mesh_io_interface = MeshIOInterface()
    #mesh_io_interface = PyMeshInterface()
    mesh_io_interface = TrimeshInterface()

    # Reading mesh
    print("Reading mesh... ", end='', flush=True)
    mesh_vertices, mesh_faces, mesh_normals, mesh_tcoords = mesh_io_interface.read(mesh_file)
    print("Done.")

    # Optional mesh for the normals
    if len(sys.argv) >= 4:
        print("Reading mesh for the normals... ", end='', flush=True)
        _, _, mesh_normals, _ = mesh_io_interface.read(sys.argv[3])
        print("Done.")

    # Cleaning mesh
    print("Cleaning mesh... ", end='', flush=True)
    num_vertices = mesh_vertices.shape[0]
    num_faces = mesh_faces.shape[0]
    mesh_vertices, mesh_faces, mesh_normals, mesh_tcoords = mesh_io_interface.clean(mesh_vertices, mesh_faces, mesh_normals, mesh_tcoords)
    print(f"Done ({mesh_vertices.shape[0] - num_vertices} vertices & {mesh_faces.shape[0] - num_faces} faces).")

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
    mesh_io_interface.write(mesh_file[:-4] + "_displaced.stl", mesh_vertices_displaced, mesh_faces)
    print("Done.")

    print("Writing difference mesh... ", end='', flush=True)
    mesh_io_interface.write(mesh_file[:-4] + "_difference.stl", vertices_diff, faces_diff)
    print("Done.")

