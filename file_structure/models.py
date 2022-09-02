import struct
from .object_3d import PolygonalFace, Vertex, VertexNormal, VertexTexture
from .utils.common_functions import to_float, to_int


class FacePS2Model:
    magic_number = bytearray([0x03,0x00,0xFF,0xFF])

    def __init__(self,model_bytes:bytes):
        self.model_bytes = model_bytes
        self.validate()
        self.pieces_total = to_int(self.model_bytes[32 : 36])
        self.pieces_start_address = to_int(self.model_bytes[36 : 40])
        self.pieces_end_address =  to_int(self.model_bytes[44 : 48])
        self.vertex_list = []
        self.vertex_normal_list = []
        self.vertex_texture_list = []
        self.polygonal_faces_list = []
        self.load_textures()
        self.set_pieces()
        self.read_pieces()

    def validate(self):
        """
        Function to check if we have a proper PES PS2 Model
        """
        if self.magic_number != self.model_bytes[:4]:
            raise ValueError("Not a PS2 face model!")
        return True

    def set_pieces(self):
        """
        A PS2 Model is divided by pieces or parts, called it as you want
        here we get all the pieces bytes into a list from the whole model bytes
        """
        pieces_bytes = self.model_bytes[self.pieces_start_address : self.pieces_end_address]
        sum_address = 0
        self.pieces = []
        i = 0
        while i < self.pieces_total:
            piece_size = to_int(pieces_bytes[sum_address : sum_address + 4])
            self.pieces.append(pieces_bytes[sum_address : sum_address + piece_size])
            sum_address += piece_size
            i +=1

    def read_pieces(self):
        vertex_size = 6 # 3 int16
        tri_counter = 0
        for piece in self.pieces:
            sum1 = 2
            sum2 = 4
            #print("part #", i)
            vertex_in_piece = piece[to_int(piece[8:12]) + 96 + sum1]
            #print("vertex ",vertex_in_piece)
            vertex_start_address = to_int(piece[8:12]) + 96 + sum2
            if vertex_in_piece%2!=0:
                # if the number of vertes is not pair then we need to incress the movement of bytes by two
                sum1+=2
                sum2+=2
            """
            """
            normals_in_piece = piece[vertex_in_piece * vertex_size + vertex_start_address + sum1]
            #print("normals ", normals_in_piece)
            normals_start_address = vertex_in_piece * vertex_size + vertex_start_address + sum2
            uv_in_piece = piece[normals_in_piece * vertex_size + normals_start_address + sum1]
            #print("uv ", uv_in_piece)
            uv_start_address = normals_in_piece * vertex_size + normals_start_address + sum2
            # Load vertex
            self.load_vertex(piece, vertex_in_piece, vertex_start_address)
            # Load Normals
            self.load_vertex_normal(piece, normals_in_piece, normals_start_address)
            # Load UV
            self.load_vextex_texture(piece, uv_in_piece, uv_start_address)
            # Load triangles
            self.load_polygonal_faces(piece, tri_counter)
            tri_counter+=vertex_in_piece

    def load_textures(self):
        total_textures,texture_offset = struct.unpack('<II', self.model_bytes[56:64])

        self.texture_list = [texture for texture in struct.unpack(f'<{total_textures}I',self.model_bytes[texture_offset:texture_offset+total_textures*4])]
        

    def load_vertex(self, piece, vertex_in_piece, vertex_start_address):
        vertex_size = 6 # 3 int16
        factor = 0.001953
        # Load vertex
        for j in range(vertex_in_piece):
            pos = vertex_start_address + j * vertex_size
            x,y,z = struct.unpack('<3h', piece[pos : pos + vertex_size])
            #print("vertex #", j)
            #print(x * factor, y * factor, z * factor)
            self.vertex_list.append(
                Vertex(
                    x * factor, 
                    y * factor *-1, 
                    z * factor,
                )
            )

    def load_vertex_normal(self, piece, normals_in_piece, normals_start_address):
        """
        Load all vertex normals into a list
        """
        vertex_size = 6 # 3 int16
        factor = 0.001953
        for j in range(normals_in_piece):
            pos = normals_start_address + j * vertex_size
            x,y,z = struct.unpack('<3h', piece[pos : pos + vertex_size])
            #print("vertex normals #", j)
            #print(x * factor, y * factor, z * factor)
            self.vertex_normal_list.append(
                VertexNormal(
                    x * factor, 
                    y * factor *-1, 
                    z * factor,
                )
            )

    def load_vextex_texture(self, piece, uv_in_piece, uv_start_address):
        """
        Load all vertex texture (uv map coordinates) into a list
        """
        validate_textures_id = [0x6f,0x72,0x64]

        uv_size = 4 # 3 int16
        factor_uv = 0.000244140625 #0.000244
        for j in range(uv_in_piece):
            pos = uv_start_address + j * uv_size
            u, v = struct.unpack('<2h', piece[pos : pos + uv_size])
            #print("vertex texture #", j)
            #print(u * factor_uv, v * factor_uv,)
            self.vertex_texture_list.append(
                VertexTexture(
                    u * factor_uv, 
                    1 - v * factor_uv*0.5, 
                )
            )

    def load_polygonal_faces(self, piece: bytearray, tri_counter:int):
        """
        Load all polygonal faces into a list
        """
        tri_idx = bytearray([0x01, 0x00, 0x00, 0x05, 0x01, 0x01, 0x00, 0x01])
        tri_start_address = piece.find(tri_idx) + len(tri_idx)
        tri_size = piece[tri_start_address + 2] * 0x8
        tri_data = piece[tri_start_address + 4 : tri_start_address + 4 + tri_size]
        tstrip_index_list = [int((x - 32768)/4) + tri_counter if x >= 32768 else int((x)/4) + tri_counter for x in struct.unpack(f'<{int(len(tri_data)/2)}H', tri_data)]
        for k in range(len(tstrip_index_list)-2):
            if (tstrip_index_list[k] != tstrip_index_list[k + 1]) and (tstrip_index_list[k + 1] != tstrip_index_list[k + 2]) and (tstrip_index_list[k + 2] != tstrip_index_list[k]):
                if k & 1:
                    self.polygonal_faces_list.append(
                        PolygonalFace(
                            tstrip_index_list[k + 1],
                            tstrip_index_list[k],
                            tstrip_index_list[k + 2]
                        )
                    )
                else:
                    self.polygonal_faces_list.append(
                        PolygonalFace(
                            tstrip_index_list[k],
                            tstrip_index_list[k + 1],
                            tstrip_index_list[k + 2]
                        )
                    )
                k+=3




