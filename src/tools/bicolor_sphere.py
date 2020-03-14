#!/usr/bin/env python3

import numpy as np

import meshdd
from meshdd.tools import shapes


# Default values for the parameters
defaults = {
    'Ntheta': 501,
    'Nphi': 501,
    'radius': 50,
    'threshold': 128,
    'depth': 1.2,
}


def create_bicolor_sphere(texture,
                          Ntheta=defaults['Ntheta'],
                          Nphi=defaults['Nphi'],
                          radius=defaults['radius'],
                          threshold=defaults['threshold'],
                          reverse=False,
                          depth=defaults['depth'],
                          verbose=False):
    """ Split a sphere in two parts based on a given texture. """

    # Verbose messages
    def info(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # Creating sphere mesh
    info("Creating sphere mesh... ", end='', flush=True)
    vertices, faces, normals, tcoords = shapes.create_sphere(Ntheta, Nphi)
    vertices *= radius
    info("Done.")

    # Reading texture image if needed
    if type(texture) is str:
        info("Reading texture... ", end='', flush=True)
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
        description="Create a bicolor sphere from a texture",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("texture", type=str, nargs=1,
                        help="Image used to split the mesh in two color")
    parser.add_argument("--Ntheta", type=int, default=defaults['Ntheta'],
                        help="Number of discretization points for the longitude")
    parser.add_argument("--Nphi", type=int, default=defaults['Nphi'],
                        help="Number of discretization points for the latitude")
    parser.add_argument("--radius", type=float, default=defaults['radius'],
                        help="Sphere radius")
    parser.add_argument("--threshold", type=float, default=defaults['threshold'],
                        help="Threshold value from the image used to split the sphere."
                             "By default, vertices corresponding to values above the threshold are carved.")
    parser.add_argument("--reverse", action="store_true",
                        help="Vertices below the threshold are carved.")
    parser.add_argument("--depth", type=float, default=defaults['depth'],
                        help="Displacement depth")
    parser.add_argument("--output", type=str, default="sphere.stl",
                        help="Output file name")
    options = parser.parse_args()

    # Generating meshes
    displaced_vertices, displaced_faces, diff_vertices, diff_faces = create_bicolor_sphere(
        texture=options.texture[0],
        Ntheta=options.Ntheta, Nphi=options.Nphi,
        radius=options.radius, threshold=options.threshold,
        reverse=options.reverse, depth=options.depth,
        verbose=True)

    # Writing resulting mesh
    filename_prefix, filename_extension = os.path.splitext(options.output)

    #mesh_interface = meshdd.tools.MeshIOInterface()
    #mesh_interface = meshdd.tools.PyMeshInterface()
    mesh_interface = meshdd.tools.TriMeshInterface()

    print("Writing displaced mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_displaced" + filename_extension, displaced_vertices, displaced_faces)
    print("Done.")

    print("Writing difference mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_difference" + filename_extension, diff_vertices, diff_faces)
    print("Done.")


if __name__ == "__main__":
    main()
