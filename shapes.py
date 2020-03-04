#!/usr/bin/env python3

def create_sphere(Ntheta, Nphi):
    import numpy as np

    # Discretizing parameters space
    theta = np.linspace(0, 2*np.pi, Ntheta+1)[:-1]
    phi = np.linspace(-np.pi/2, np.pi/2, Nphi)[1:-1]
    theta2d, phi2d = np.meshgrid(theta, phi)

    # Mesh size
    num_vertices = theta.size * phi.size + 2
    num_triangles = 2 * theta.size + 2 * theta.size * (phi.size - 1)

    # Assembling texture coordinates
    tcoords = np.empty((num_vertices, 2))
    tcoords[0, :] = [0, -np.pi/2]
    tcoords[1:-1, 0] = theta2d.flatten()
    tcoords[1:-1, 1] = phi2d.flatten()
    tcoords[-1, :] = [0, np.pi/2]

    # Assembling vertices coordinates
    vertices = np.empty((num_vertices, 3))
    vertices[:, 0] = np.cos(tcoords[:, 1]) * np.cos(tcoords[:, 0])
    vertices[:, 1] = np.cos(tcoords[:, 1]) * np.sin(tcoords[:, 0])
    vertices[:, 2] = np.sin(tcoords[:, 1])

    # Assembling triangles
    triangles = np.empty((num_triangles, 3), dtype=np.int64)

    # South pole
    triangle_archetype = np.array([0, 2, 1], dtype=np.int64)
    triangles[:theta.size, :] = triangle_archetype + np.arange(theta.size).reshape(-1, 1)
    triangles[:theta.size, 0] = 0
    triangles[theta.size-1, 1] -= theta.size

    # Middle part low
    middle_half_size = theta.size * (phi.size - 1)
    triangle_archetype = 1 + np.array([theta.size, 0, 1], dtype=np.int64)
    triangles[theta.size:theta.size + middle_half_size, :] = triangle_archetype + np.arange(middle_half_size).reshape(-1, 1)
    triangles[2*theta.size-1:theta.size + middle_half_size:theta.size, 2] -= theta.size

    # Middle part high
    triangle_archetype = 1 + np.array([theta.size, 1, 1 + theta.size], dtype=np.int64)
    triangles[theta.size + middle_half_size:theta.size + 2*middle_half_size, :] = triangle_archetype + np.arange(middle_half_size).reshape(-1, 1)
    triangles[2*theta.size + middle_half_size - 1:theta.size + 2*middle_half_size:theta.size, 1:3] -= theta.size

    # North pole
    triangle_archetype = theta.size * (phi.size - 1) + 1 + np.array([0, 1, theta.size], dtype=np.int64)
    triangles[-theta.size:, :] = triangle_archetype + np.arange(theta.size).reshape(-1, 1)
    triangles[-theta.size:, 2] = num_vertices - 1
    triangles[-1, 1] -= theta.size

    return vertices, triangles, vertices.copy(), (tcoords + [0, np.pi/2]) / [2*np.pi, np.pi]


