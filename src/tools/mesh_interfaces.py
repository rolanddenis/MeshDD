import numpy as np

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

    def clean(self, vertices, faces, normals=None, tcoords=None, tol=1e-12):
        import pymesh

        # Removing duplicated vertices
        vertices, faces, info = pymesh.remove_duplicated_vertices_raw(vertices, faces, tol)

        if normals is not None:
            cleaned_normals = np.empty((vertices.shape[0], normals.shape[1]), dtype=normals.dtype)
            cleaned_normals[info['index_map'], :] = normals
        else:
            cleaned_normals = None

        if tcoords is not None:
            cleaned_tcoords = np.empty((vertices.shape[0], tcoords.shape[1]), dtype=tcoords.dtype)
            cleaned_tcoords[info['index_map'], :] = tcoords
        else:
            cleaned_tcoords = None

        # Removing degenerated triangles
        # FIXME: Returned vertices are modified (order probably) without a way
        #        to get the map so that to update the attributes...
        #vertices, faces, info = pymesh.remove_degenerated_triangles_raw(vertices, faces)

        # Removing degenerated triangles
        # Only the triangles with duplicated vertices
        mask = np.logical_or(np.logical_or(faces[:, 0] == faces[:, 1],
                                           faces[:, 0] == faces[:, 2]),
                             faces[:, 1] == faces[:, 2])
        faces = faces[np.logical_not(mask), :]

        return vertices, faces, cleaned_normals, cleaned_tcoords

    def write(self, mesh_file, vertices, faces):
        import pymesh
        pymesh.save_mesh_raw(mesh_file, vertices, faces)

class TriMeshInterface:
    """ Mesh reader/writer interface for trimesh """

    def read(self, mesh_file):
        assert mesh_file[-4:] == '.ply', "Only PLY format for input mesh"

        # Read mesh (no cleaning before extracting vertex attributes)
        import trimesh
        mesh = trimesh.load(mesh_file, process=False)

        # Check that it is triangulated
        assert mesh.faces.shape[1] == 3, "Mesh must be triangulated!"

        # Additional fields are not extracted as vertex attributes
        # but still accessible in the metadata
        extra_fields = mesh.metadata['ply_raw']['vertex']['data']

        # Extract normals
        if 'vertex_normals' in mesh._cache:
            normals = mesh.vertex_normals
        elif all(k in extra_fields.dtype.names for k in ('nx', 'ny', 'nz')):
            normals = np.hstack((extra_fields['nx'][:, None],
                                 extra_fields['ny'][:, None],
                                 extra_fields['nz'][:, None]))
        else:
            normals = None

        # Extract texture coordinates
        if all(k in extra_fields.dtype.names for k in ('s', 't')):
            tcoords = np.hstack((extra_fields['s'][:, None],
                                 extra_fields['t'][:, None]))
        else:
            tcoords = None

        return mesh.vertices, mesh.faces, normals, tcoords

    def clean(self, vertices, faces, normals=None, tcoords=None, tol=1e-12):
        """ Remove duplicated vertices and degenerated triangles """

        import trimesh

        # Creating mesh
        # Not adding vertex normals since they disappear during cleaning pass
        mesh = trimesh.Trimesh(vertices=vertices,
                               faces=faces,
                               process=False)

        # Populating vertex attributes
        if tcoords is not None:
            mesh.vertex_attributes['tcoords'] = tcoords
        if normals is not None:
            mesh.vertex_attributes['normals'] = normals

        # Cleaning
        trimesh.constants.tol.merge = tol
        mesh.merge_vertices()
        mesh.remove_degenerate_faces()

        return (mesh.vertices,
                mesh.faces,
                mesh.vertex_attributes.get('normals', None),
                mesh.vertex_attributes.get('tcoords', None))


    def write(self, mesh_file, vertices, faces):
        import trimesh

        # Creating mesh
        mesh = trimesh.Trimesh(vertices=vertices,
                               faces=faces,
                               process=False)

        trimesh.exchange.export.export_mesh(mesh, mesh_file)



