import struct
from io import BytesIO

from file_structure import to_signed_bytes

MODEL_MAGIC_NUMBER = bytearray([0x03, 0x00, 0xFF, 0xFF])


def openBaseModel(uncompress_bin_file, vertex_texture_list: list):
    uncompress_bin_file.seek(0,2)

    uncompress_bin_size = uncompress_bin_file.tell()

    uncompress_bin_file.seek(0,0)
    
    total_files = struct.unpack('<I', uncompress_bin_file.read(4))[0]

    start_table_files = struct.unpack('<I', uncompress_bin_file.read(4))[0]

    uncompress_bin_file.seek(start_table_files, 0)

    file_offset_table = [struct.unpack("<I", uncompress_bin_file.read(4))[0] for i in range(total_files)]
    
    i = 0
    count_vertex = 0
    while i < 1:
        uncompress_bin_file.seek(file_offset_table[i])
        if i != len(file_offset_table) - 1:
            sub_file_size = file_offset_table[i + 1] - file_offset_table[i]
        else:
            sub_file_size = uncompress_bin_size - file_offset_table[i]
        
        try:
            mdl_1 = write_vertex(uncompress_bin_file.read(sub_file_size), i, vertex_texture_list)
        except Exception as e:
            print(e)
        i += 1

    uncompress_bin_file.seek(file_offset_table[0],0)
    uncompress_bin_file.write(mdl_1)

    uncompress_bin_file.seek(0,0)
    return uncompress_bin_file.read()


def write_vertex(container:bytes, file_number:int, vertices_texture:list):
    valid_textures_list = [0x64, 0x6F, 0x72]

    mdl = BytesIO(container)

    if mdl.read(4) != MODEL_MAGIC_NUMBER:
        raise Exception(f"Sub file {file_number} is not a 3D model file")

    mdl.seek(32, 0)
    total_parts = struct.unpack("<I", mdl.read(4))[0]
    #print("total parts in this model are: ", total_parts)
    part_start_offset = struct.unpack("<I", mdl.read(4))[0]
    mdl.seek(56, 0)
    total_txs =  struct.unpack("<I", mdl.read(4))[0]
    txs_mapping_start =  struct.unpack("<I", mdl.read(4))[0]
    mdl.seek(txs_mapping_start, 0)
    #print("texture mapping on this model")
    
    valid_textures_indexes = [
        i 
        for i, txs_id in enumerate(
            struct.unpack(
                f"{total_txs}I",
                mdl.read(total_txs * 4)
            )
        )
        if txs_id in valid_textures_list
    ]
    factor = 0.001953
    i = 0
    vertex_count = 0
    while i < total_parts:
        #print("part ",i, " offset: ", part_start_offset)
        mdl.seek(part_start_offset,0)
        part_size = struct.unpack("<I", mdl.read(4))[0]

        #print("part #", i)
        mdl.seek(4,1)
        part_info_start = struct.unpack("<I", mdl.read(4))[0]
        mdl.seek(part_start_offset + 52,0)
        txs_id =  struct.unpack("<I", mdl.read(4))[0]
        #print("this part use texture id: ", txs_id)

        mdl.seek(part_start_offset+part_info_start+88,0)
        

        vertex_in_piece = struct.unpack("<H", mdl.read(2))[0]

        if txs_id in valid_textures_indexes:

        
            mdl.seek(10,1)
            
            mdl.seek(vertex_in_piece*6,1)

            #"""
            if vertex_in_piece%2!=0:
                # if the number of vertes is not pair then we need to incress the movement of bytes by two
                mdl.seek(2,1)
            mdl.seek(4,1)
            mdl.seek(vertex_in_piece*6,1)
            
            if vertex_in_piece%2!=0:
                # if the number of vertes is not pair then we need to incress the movement of bytes by two
                mdl.seek(2,1)
                
            mdl.seek(4,1)
            factor_uv = 0.000244140625
            for j in range(vertex_in_piece):
                v,t = round(vertices_texture[vertex_count + j][0]/factor_uv), round((1 - vertices_texture[vertex_count + j][1]) / factor_uv)
                mdl.write(to_signed_bytes(v))
                mdl.write(to_signed_bytes(t))
            vertex_count += vertex_in_piece

            #print(i)
            #if i == 0:
                #print("Saliendo del loop")
                #break  
        
        part_start_offset += part_size
        i += 1
        #"""
        #with open('file.bin','wb') as file:
        #    mdl.seek(0,0)
        #    file.write(mdl.read())
    mdl.seek(0,0)
    return mdl.read()