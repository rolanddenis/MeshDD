def create_sphere(Nphi, Ntheta):
    """
    Generates the mesh of an UV sphere

    Parameters
    ----------
    Nphi: int
        Number of discretization points for the longitude
    Ntheta: int
        Number of discretization points for the latitude

    Returns
    -------
    vertices: (n, 3) float
        Vertices of the sphere mesh
    faces: (m, 3) int
        Vertices index composing each face
    normals: (n, 3) float
        Sphere normal for each vertice
    tcoords: (n, 2) float
        Texture coordinates for each vertice
    """

    import numpy as np

    # Discretizing parameters space
    phi = np.linspace(0, 2*np.pi, Nphi+1)[:-1]
    theta = np.linspace(-np.pi/2, np.pi/2, Ntheta)[1:-1]
    phi2d, theta2d = np.meshgrid(phi, theta)

    # Mesh size
    num_vertices = phi.size * theta.size + 2
    num_triangles = 2 * phi.size + 2 * phi.size * (theta.size - 1)

    # Assembling texture coordinates
    tcoords = np.empty((num_vertices, 2))
    tcoords[0, :] = [0, -np.pi/2]
    tcoords[1:-1, 0] = phi2d.flatten()
    tcoords[1:-1, 1] = theta2d.flatten()
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
    triangles[:phi.size, :] = triangle_archetype + np.arange(phi.size).reshape(-1, 1)
    triangles[:phi.size, 0] = 0
    triangles[phi.size-1, 1] -= phi.size

    # Middle part low
    middle_half_size = phi.size * (theta.size - 1)
    triangle_archetype = 1 + np.array([phi.size, 0, 1], dtype=np.int64)
    triangles[phi.size:phi.size + middle_half_size, :] = triangle_archetype + np.arange(middle_half_size).reshape(-1, 1)
    triangles[2*phi.size-1:phi.size + middle_half_size:phi.size, 2] -= phi.size

    # Middle part high
    triangle_archetype = 1 + np.array([phi.size, 1, 1 + phi.size], dtype=np.int64)
    triangles[phi.size + middle_half_size:phi.size + 2*middle_half_size, :] = triangle_archetype + np.arange(middle_half_size).reshape(-1, 1)
    triangles[2*phi.size + middle_half_size - 1:phi.size + 2*middle_half_size:phi.size, 1:3] -= phi.size

    # North pole
    triangle_archetype = phi.size * (theta.size - 1) + 1 + np.array([0, 1, phi.size], dtype=np.int64)
    triangles[-phi.size:, :] = triangle_archetype + np.arange(phi.size).reshape(-1, 1)
    triangles[-phi.size:, 2] = num_vertices - 1
    triangles[-1, 1] -= phi.size

    return vertices, triangles, vertices.copy(), (tcoords + [0, np.pi/2]) / [2*np.pi, np.pi]


def create_torus(Nx, Ny, R=1., r=0.4):
    """
    Generates the mesh of a torus

    Parameters
    ----------
    Nx: int
        Number of discretization points along the major radius
    Ny: int
        Number of discretization points along the minor radius
    R: float
        The major radius
    r: float
        The minor radius

    Returns
    -------
    vertices: (n, 3) float
        Vertices of the torus mesh
    faces: (m, 3) int
        Vertices index composing each face
    normals: (n, 3) float
        Sphere normal for each vertice
    tcoords: (n, 2) float
        Texture coordinates for each vertice
    """

    import numpy as np

    # Discretizing parameters space
    x = np.linspace(0, 2*np.pi, Nx+1)[:-1]
    y = np.linspace(0, 2*np.pi, Ny+1)[:-1]
    x2d, y2d = np.meshgrid(x, y)

    # Mesh size
    num_vertices = Nx * Ny
    num_triangles = 2 * num_vertices

    # Assembling texture coordinates
    tcoords = np.hstack((x2d.reshape(-1, 1), y2d.reshape(-1, 1)))

    # Assembling vertices coordinates
    vertices = np.empty((num_vertices, 3))
    vertices[:, 0] = (R + r * np.cos(tcoords[:, 1])) * np.cos(tcoords[:, 0])
    vertices[:, 1] = (R + r * np.cos(tcoords[:, 1])) * np.sin(tcoords[:, 0])
    vertices[:, 2] = r * np.sin(tcoords[:, 1])

    # Assembling normals
    normals = np.empty((num_vertices, 3))
    normals[:, 0] = np.cos(tcoords[:, 1]) * np.cos(tcoords[:, 0])
    normals[:, 1] = np.cos(tcoords[:, 1]) * np.sin(tcoords[:, 0])
    normals[:, 2] = np.sin(tcoords[:, 1])

    # Assembling triangles
    triangles = np.empty((num_triangles, 3), dtype=np.int64)

    # Low part
    triangle_archetype = np.array([0, 1, Nx], dtype=np.int64)
    triangles[:num_vertices, :] = triangle_archetype + np.arange(num_vertices).reshape(-1, 1)
    triangles[Nx - 1:num_vertices:Nx, 1] -= Nx
    triangles[num_vertices - Nx:num_vertices, 2] -= num_vertices

    # High part
    triangle_archetype = np.array([1, Nx + 1, Nx], dtype=np.int64)
    triangles[-num_vertices:, :] = triangle_archetype + np.arange(num_vertices).reshape(-1, 1)
    triangles[-num_vertices + Nx - 1::Nx, :2] -= Nx
    triangles[-Nx:, 1:] -= num_vertices

    return vertices, triangles, normals, tcoords / (2 * np.pi)
