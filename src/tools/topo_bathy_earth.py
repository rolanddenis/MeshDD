#!/usr/bin/env python3

import numpy as np

import meshdd
from meshdd.tools import shapes

# Default values for the parameters
# Tuned for https://visibleearth.nasa.gov/images/73963
#  and https://visibleearth.nasa.gov/images/73934
#  in resolution 21600x10800
defaults = {
    'Ntheta': 501,
    'Nphi': 501,
    'radius': 50,
    'topo_depth': 5,
    'topo_threshold': 5,
    'topo_reverse': False,
    'topo_sigma': 10,
    'bathy_depth': 5,
    'bathy_threshold': 5,
    'bathy_reverse': True,
    'bathy_sigma': 10,
}


def create_topo_bathy_earth(topo_texture, bathy_texture,
                            Ntheta=defaults['Ntheta'],
                            Nphi=defaults['Nphi'],
                            radius=defaults['radius'],
                            topo_depth=defaults['topo_depth'],
                            topo_threshold=defaults['topo_threshold'],
                            topo_reverse=defaults['topo_reverse'],
                            topo_sigma=defaults['topo_sigma'],
                            bathy_depth=defaults['bathy_depth'],
                            bathy_threshold=defaults['bathy_threshold'],
                            bathy_reverse=defaults['bathy_reverse'],
                            bathy_sigma=defaults['bathy_sigma'],
                            verbose=False):
    """
    From topography and bathymetry textures, split land and sea and displace
    following the depth and altitude.
    """

    from scipy.ndimage.filters import gaussian_filter

    # Verbose messages
    def info(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # Creating sphere mesh
    info("Creating sphere mesh... ", end='', flush=True)
    vertices, faces, normals, tcoords = shapes.create_sphere(Ntheta, Nphi)
    vertices *= radius
    info("Done.")

    def read_texture(file_name):
        import imageio
        import PIL.Image
        PIL.Image.MAX_IMAGE_PIXELS = 20000**2 # Should also be None if the image is from trusted source...
        return meshdd.get_texture_from_image(imageio.imread(file_name))

    from scipy.ndimage.filters import gaussian_filter

    # Reading topography texture image if needed
    if type(topo_texture) is str:
        info("Reading topography texture... ", end='', flush=True)
        topo_texture = read_texture(topo_texture)
        info("Done.")

    if topo_reverse:
        topo_texture = 255 - topo_texture

    # Reading bathymetry texture image if needed
    if type(bathy_texture) is str:
        info("Reading bathymetry texture... ", end='', flush=True)
        bathy_texture = read_texture(bathy_texture)
        info("Done.")

    if bathy_reverse:
        bathy_texture = 255 - bathy_texture

    # Smoothing textures
    info("Smoothing textures... ", end='', flush=True)
    if topo_sigma is not None:
        topo_texture = gaussian_filter(topo_texture.astype(float), sigma=topo_sigma)
    if bathy_sigma is not None:
        bathy_texture = gaussian_filter(bathy_texture.astype(float), sigma=bathy_sigma)
    info("Done.")

    # Carving the sea
    info("Carving the sea... ", end='', flush=True)
    vertex_color = meshdd.get_vertex_color_from_texture(tcoords, bathy_texture)
    if vertex_color.ndim > 1:
        vertex_color = np.mean(vertex_color, axis=1)

    displace_mask = vertex_color >= bathy_threshold
    land_vertices = meshdd.displace_vertices(vertices, normals, -bathy_depth * vertex_color / 255., displace_mask)
    info("Done.")

    # Sea mesh as the difference with the sphere
    info("Sea mesh... ", end='', flush=True)
    sea_vertices, sea_faces = meshdd.get_boolean_difference(vertices, land_vertices, faces, displace_mask)
    info("Done.")

    # Bringing the mountains out
    info("Bringing the mountains out... ", end='', flush=True)
    vertex_color = meshdd.get_vertex_color_from_texture(tcoords, topo_texture)
    if vertex_color.ndim > 1:
        vertex_color = np.mean(vertex_color, axis=1)

    displace_mask = vertex_color >= topo_threshold
    land_vertices = meshdd.displace_vertices(land_vertices, normals, topo_depth * vertex_color / 255., displace_mask)
    info("Done.")

    return (land_vertices, faces,
            sea_vertices, sea_faces)


def main():
    import argparse
    import os

    # Command-line parameters
    parser = argparse.ArgumentParser(
        description="Create an earth mesh with amplified topography and bathemetry",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("topo_texture", type=str, nargs=1,
                        help="Topography image")
    parser.add_argument("bathy_texture", type=str, nargs=1,
                        help="Bathymetry image")
    parser.add_argument("--Ntheta", type=int, default=defaults['Ntheta'],
                        help="Number of discretization points for the longitude")
    parser.add_argument("--Nphi", type=int, default=defaults['Nphi'],
                        help="Number of discretization points for the latitude")
    parser.add_argument("--radius", type=float, default=defaults['radius'],
                        help="Sphere radius")
    parser.add_argument("--topo_depth", type=float, default=defaults['topo_depth'],
                        help="Maximum displacement depth for the topography")
    parser.add_argument("--bathy_depth", type=float, default=defaults['bathy_depth'],
                        help="Maximum displacement depth for the bathymetry")
    parser.add_argument("--topo_threshold", type=float, default=defaults['topo_threshold'],
                        help="Displacement threshold for the topography")
    parser.add_argument("--bathy_threshold", type=float, default=defaults['bathy_threshold'],
                        help="Displacement threshold for the bathymetry")
    parser.add_argument("--topo_reverse", type=float, default=defaults['topo_reverse'],
                        help="Reverse topography values")
    parser.add_argument("--bathy_reverse", type=float, default=defaults['bathy_reverse'],
                        help="Reverse bathymetry values")
    parser.add_argument("--topo_sigma", type=float, default=defaults['topo_sigma'],
                        help="Standard deviation of the Gaussian blur kernel applied to topography texture")
    parser.add_argument("--bathy_sigma", type=float, default=defaults['bathy_sigma'],
                        help="Standard deviation of the Gaussian blur kernel applied to bathymetry texture")
    parser.add_argument("--output", type=str, default="earth.stl",
                        help="Output file name")
    options = parser.parse_args()

    # Generating meshes
    land_vertices, land_faces, sea_vertices, sea_faces = create_topo_bathy_earth(
        topo_texture=options.topo_texture[0],
        bathy_texture=options.bathy_texture[0],
        Ntheta=options.Ntheta, Nphi=options.Nphi,
        radius=options.radius,
        topo_depth=options.topo_depth,
        topo_threshold=options.topo_threshold,
        topo_reverse=options.topo_reverse,
        topo_sigma=options.topo_sigma,
        bathy_depth=options.bathy_depth,
        bathy_threshold=options.bathy_threshold,
        bathy_reverse=options.bathy_reverse,
        bathy_sigma=options.bathy_sigma,
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


if __name__ == "__main__":
    main()
