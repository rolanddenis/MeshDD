#!/usr/bin/env python3

import numpy as np

import meshdd
from meshdd.tools import shapes

# Default values for the parameters
defaults = {
    'Ntheta': 501,
    'Nphi': 501,
    'radius': 50,
    'depth': 1.2,
    'sigma': 1,
}


def create_tricolor_earth(texture,
                          Ntheta=defaults['Ntheta'],
                          Nphi=defaults['Nphi'],
                          radius=defaults['radius'],
                          depth=defaults['depth'],
                          sigma=defaults['sigma'],
                          verbose=False):
    """
    From a texture, split a sphere in land, see and ice parts.

    Tuned for Earth images from https://visibleearth.nasa.gov/images/57730
    """

    from scipy.ndimage.filters import gaussian_filter

    # Verbose messages
    def info(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # Creating sphere mesh
    info("Creating sphere mesh...", end='', flush=True)
    vertices, faces, normals, tcoords = shapes.create_sphere(Ntheta, Nphi)
    vertices *= radius
    info("Done.")

    # Reading texture image if needed
    if type(texture) is str:
        info("Reading texture...", end='', flush=True)
        import imageio
        texture = meshdd.get_texture_from_image(imageio.imread(texture))
        info("Done.")

    # Calculating land, sea and ice masks
    info("Calculating land, sea and ice mask...", end='', flush=True)
    ice_mask = np.logical_and(texture.mean(axis=2) >= 200, texture[:, :, -1] >= np.max(texture[:, :, :2], axis=2))
    sea_mask = texture[:, :, -1] >= 1.5*np.max(texture[:, :, :1], axis=2)
    land_mask = np.logical_not(np.logical_or(ice_mask, sea_mask))
    land_mask = gaussian_filter(land_mask.astype(float), sigma=sigma) >= 0.5
    ice_mask = gaussian_filter(ice_mask.astype(float), sigma=sigma) >= 0.5
    sea_mask = np.logical_not(np.logical_or(land_mask, ice_mask))
    info("Done.")

    # Displace and difference for the sea
    info("Displacing and difference for the sea part...", end='', flush=True)
    displace_mask = meshdd.get_vertex_color_from_texture(tcoords, sea_mask)
    tmp_vertices = meshdd.displace_vertices(vertices, normals, -depth, displace_mask)
    sea_vertices, sea_faces = meshdd.get_boolean_difference(vertices, tmp_vertices, faces, displace_mask)
    info("Done.")

    # Displace and difference for the ice
    info("Displacing and difference for the ice part...", end='', flush=True)
    displace_mask = meshdd.get_vertex_color_from_texture(tcoords, ice_mask)
    land_vertices = meshdd.displace_vertices(tmp_vertices, normals, -depth, displace_mask)
    ice_vertices, ice_faces = meshdd.get_boolean_difference(tmp_vertices, land_vertices, faces, displace_mask)
    info("Done.")

    return (land_vertices, faces,
            sea_vertices, sea_faces,
            ice_vertices, ice_faces)


def main():
    import argparse
    import os

    # Command-line parameters
    parser = argparse.ArgumentParser(
        description="Create an earth mesh with three colors for land, sea and ice",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("texture", type=str, nargs=1,
                        help="Earth image from https://visibleearth.nasa.gov/images/57730")
    parser.add_argument("--Ntheta", type=int, default=defaults['Ntheta'],
                        help="Number of discretization points for the longitude")
    parser.add_argument("--Nphi", type=int, default=defaults['Nphi'],
                        help="Number of discretization points for the latitude")
    parser.add_argument("--radius", type=float, default=defaults['radius'],
                        help="Sphere radius")
    parser.add_argument("--depth", type=float, default=defaults['depth'],
                        help="Displacement depth")
    parser.add_argument("--sigma", type=float, default=defaults['sigma'],
                        help="Standard deviation used to define the Gaussian blur kernel when splitting texture")
    parser.add_argument("--output", type=str, default="earth.stl",
                        help="Output file name")
    options = parser.parse_args()

    # Generating meshes
    land_vertices, land_faces, sea_vertices, sea_faces, ice_vertices, ice_faces = create_tricolor_earth(
        texture=options.texture[0],
        Ntheta=options.Ntheta, Nphi=options.Nphi,
        radius=options.radius, sigma=options.sigma,
        depth=options.depth,
        verbose=True)

    # Writing resulting mesh
    filename_prefix, filename_extension = os.path.splitext(options.output)

    #mesh_interface = meshdd.tools.MeshIOInterface()
    #mesh_interface = meshdd.tools.PyMeshInterface()
    mesh_interface = meshdd.tools.TriMeshInterface()

    print("Writing land mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_land" + filename_extension, land_vertices, land_faces)
    print("Done.")

    print("Writing sea mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_sea" + filename_extension, sea_vertices, sea_faces)
    print("Done.")

    print("Writing ice mesh... ", end='', flush=True)
    mesh_interface.write(filename_prefix + "_ice" + filename_extension, ice_vertices, ice_faces)
    print("Done.")


if __name__ == "__main__":
    main()
