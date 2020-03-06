#!/usr/bin/env python3

import numpy as np

import meshdd

# Default values for the parameters
defaults = {
    'threshold': 128,
    'scale': 50,
    'depth': 0.5,
}

def create_bicolor_mesh(vertices, faces, normals, tcoords, texture,
                        threshold=defaults['threshold'],
                        depth=defaults['depth'],
                        reverse=False,
                        verbose=False):
    """ Split a mesh in two parts based on a given texture. """

    # Verbose messages
    def info(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # Reading texture image if needed
    if type(texture) is str:
        info("Reading texture...", end='', flush=True)
        import imageio
        texture = meshdd.get_texture_from_image(imageio.imread(texture))
        info("Done.")

    # Displacing mesh
    info("Displacing mesh... ", end='', flush=True)
    vertex_color = meshdd.get_vertex_color_from_texture(tcoords, texture)
    if vertex_color.ndim > 1:
        vertex_color = np.mean(vertex_color, axis=1)

    displace_mask = vertex_color >= threshold
    if reverse:
        displace_mask = np.logical_not(displace_mask)

    displaced_vertices = meshdd.displace_vertices(vertices, normals, -depth, displace_mask)
    info("Done.")

    # Difference mesh
    info("Difference mesh... ", end='', flush=True)
    diff_vertices, diff_faces = meshdd.get_boolean_difference(vertices, displaced_vertices, faces, displace_mask)
    info("Done.")

    return displaced_vertices, faces, diff_vertices, diff_faces


def main():
    import argparse
    import os

    # Command-line parameters
    parser = argparse.ArgumentParser(
        description="Split a mesh in two parts based on a texture",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("mesh", type=str, nargs=1,
                        help="Mesh file (PLY only)")
    parser.add_argument("texture", type=str, nargs=1,
                        help="Image used to split the mesh in two color")
    parser.add_argument("--normals", type=str, default='',
                        help="Get normals from given mesh instead of the processed mesh")
    parser.add_argument("--scale", type=float, default=defaults['scale'],
                        help="Scale the mesh")
    parser.add_argument("--threshold", type=float, default=defaults['threshold'],
                        help="Threshold value from the image used to split the sphere."
                             "By default, vertices corresponding to values above the threshold are carved.")
    parser.add_argument("--reverse", action="store_true",
                        help="Vertices below the threshold are carved.")
    parser.add_argument("--clean", action="store_true",
                        help="Clean the mesh before processing")
    parser.add_argument("--depth", type=float, default=defaults['depth'],
                        help="Displacement depth")
    parser.add_argument("--output", type=str, default="mesh.stl",
                        help="Output file name")
    options = parser.parse_args()

    # Mesh interface
    #mesh_interface = meshdd.tools.MeshIOInterface()
    #mesh_interface = meshdd.tools.PyMeshInterface()
    mesh_interface = meshdd.tools.TriMeshInterface()

    # Reading mesh
    print("Reading mesh... ", end='', flush=True)
    vertices, faces, normals, tcoords = mesh_interface.read(options.mesh[0])
    print("Done.")

    # Optional mesh for the normals
    if options.normals:
        print("Reading mesh for the normals... ", end='', flush=True)
        _, _, normals, _ = mesh_interface.read(options.normals)
        print("Done.")

    # Cleaning mesh
    if options.clean:
        print("Cleaning mesh... ", end='', flush=True)
        num_vertices, num_faces = vertices.shape[0], faces.shape[0]
        vertices, faces, normals, tcoords = mesh_interface.clean(vertices, faces, normals, tcoords)
        print(f"Done ({vertices.shape[0] - num_vertices} vertices & {faces.shape[0] - num_faces} faces).")

    # Checking mesh
    print("Checking mesh... ", end='', flush=True)
    if tcoords is None:
        print("Missing texture coordinates!", file=sys.stderr)
        sys.exit(2)

    if normals is None:
        print("Missing normals!", file=sys.stderr)
        sys.exit(2)

    print("OK.")

    # Scaling mesh
    vertices *= options.scale

    # Some informations about the mesh
    print(f"#vertex={vertices.shape[0]} #triangles={faces.shape[0]}")
    print(f"Mesh bounds: min={np.amin(vertices, axis=0)} max={np.amax(vertices, axis=0)}")
    print(f"UV bounds: min={np.amin(tcoords, axis=0)} max={np.amax(tcoords, axis=0)}")

    # Generating meshes
    displaced_vertices, displaced_faces, diff_vertices, diff_faces = create_bicolor_mesh(
        vertices, faces, normals, tcoords, options.texture[0],
        threshold=options.threshold,
        depth=options.depth,
        reverse=options.reverse,
        verbose=True)

    # Writing resulting mesh
    filename_prefix, filename_extension = os.path.splitext(options.output)

    print("Writing displaced mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_displaced" + filename_extension, displaced_vertices, displaced_faces)
    print("Done.")

    print("Writing difference mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_difference" + filename_extension, diff_vertices, diff_faces)
    print("Done.")


if __name__ == "__main__":
    main()

