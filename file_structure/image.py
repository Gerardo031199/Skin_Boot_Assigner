from PIL import Image, ImageTk
import io
import zlib
from .utils.common_functions import to_int

class PESImage() :
    PES_IMAGE_SIGNATURE = bytearray([0x94, 0x72, 0x85, 0x29,])
    width = 0
    height = 0
    bpp = 8
    pes_idat = bytearray()
    pes_palette = bytearray()

    def from_bytes(self, pes_image_bytes:bytearray):
        magic_number = pes_image_bytes[:4]
        if not self.__valid_PESImage(magic_number): 
            raise Exception("not valid PES IMAGE")
        size = to_int(pes_image_bytes[8:12])
        pes_image_bytes = pes_image_bytes[:size]
        self.width = to_int(pes_image_bytes[20:22])
        self.height = to_int(pes_image_bytes[22:24])
        pes_palette_start = to_int(pes_image_bytes[18:20])
        pes_idat_start = to_int(pes_image_bytes[16:18])
        self.pes_palette = pes_image_bytes[pes_palette_start:pes_idat_start]
        self.pes_idat = pes_image_bytes[pes_idat_start:size]

    def __valid_PESImage(self,magic_number : bytearray):
        return magic_number == self.PES_IMAGE_SIGNATURE

    def bgr_to_bgri(self):
        for i in range(32,len(self.pes_palette),128):
            self.pes_palette[i:i+32], self.pes_palette[i+32:i+72] = self.pes_palette[i+32:i+72], self.pes_palette[i:i+32]

class PNGImage:
    PNG_SIGNATURE = bytearray([137, 80, 78, 71, 13, 10, 26, 10])
    IHDR_LENGTH = bytearray((13).to_bytes(4, byteorder='big', signed=False))
    IHDR = bytearray([73,72,68,82])
    PLTE = bytearray([80,76,84,69])
    TRNS = bytearray([116,82,78,83])
    IDAT = bytearray([73,68,65,84])
    IEND_LENGTH = bytearray(4)
    IEND = bytearray([73,69,78,68])
    iend_crc32 = bytearray(zlib.crc32(IEND).to_bytes(4, byteorder='big', signed=False))
    iend_chunk = IEND_LENGTH + IEND + iend_crc32
    TEXT = bytearray([116,69,88,116])
    keyword_author = 'Author'.encode('iso-8859-1')
    text_author = 'PES 5 Indie Team & Yerry11'.encode('iso-8859-1')
    keyword_software = 'Software'.encode('iso-8859-1')
    text_software = 'OF Team Editor'.encode('iso-8859-1')
    separator = bytearray(1)
    
    def png_from_pes_img(self, pes_img: PESImage):
        """
        Returns a PNG image from a pes image
        """
        self.pes_img = pes_img
        IHDR_DATA = (bytearray(self.pes_img.width.to_bytes(4, byteorder='big', signed=False)) 
        +  bytearray(self.pes_img.height.to_bytes(4, byteorder='big', signed=False)) 
        + bytearray([self.pes_img.bpp, 3, 0, 0, 0]))
        ihdr_crc32 = bytearray(zlib.crc32(self.IHDR + IHDR_DATA).to_bytes(4, byteorder='big', signed=False))
        ihdr_chunk = self.IHDR_LENGTH + self.IHDR + IHDR_DATA + ihdr_crc32
        palette_data = self.__pes_palette_to_RGB()
        plte_lenght = bytearray(len(palette_data).to_bytes(4, byteorder='big', signed=False))
        plte_crc32 = bytearray(zlib.crc32(self.PLTE + palette_data).to_bytes(4, byteorder='big', signed=False))
        plt_chunk = plte_lenght + self.PLTE + palette_data + plte_crc32
        trns_data = self.__pes_trns_to_alpha()
        trns_lenght = bytearray(len(trns_data).to_bytes(4, byteorder='big', signed=False))
        trns_crc32 = bytearray(zlib.crc32(self.TRNS+trns_data).to_bytes(4, byteorder='big', signed=False))
        trns_chunk = trns_lenght + self.TRNS + trns_data + trns_crc32
        idat_data = self.__pes_px_to_idat()
        idat_lenght = bytearray(len(idat_data).to_bytes(4, byteorder='big', signed=False))
        idat_crc32 = bytearray(zlib.crc32(self.IDAT + idat_data).to_bytes(4, byteorder='big', signed=False))
        idat_chunk = bytearray(idat_lenght + self.IDAT + idat_data + idat_crc32)
        author_data = bytearray(self.keyword_author + self.separator + self.text_author)
        author_lenght = bytearray(len(author_data).to_bytes(4, byteorder='big', signed=False))
        author_crc32 = bytearray(zlib.crc32(self.TEXT + author_data).to_bytes(4, byteorder='big', signed=False))
        author_chunk = bytearray(author_lenght + self.TEXT + author_data + author_crc32)

        software_data = bytearray(self.keyword_software + self.separator + self.text_software)
        software_lenght = bytearray(len(software_data).to_bytes(4, byteorder='big', signed=False))
        software_crc32 = bytearray(zlib.crc32(self.TEXT + software_data).to_bytes(4, byteorder='big', signed=False))
        software_chunk = bytearray(software_lenght + self.TEXT + software_data + software_crc32)

        self.png = self.PNG_SIGNATURE + ihdr_chunk + plt_chunk + trns_chunk + author_chunk + software_chunk + idat_chunk + self.iend_chunk

    def __png_bytes_to_tk_img(self):
        return ImageTk.PhotoImage(Image.open(io.BytesIO(self.png)).convert("RGBA"))

    def __pes_palette_to_RGB(self):
        palette_data = bytearray()
        for j in range(0, len(self.pes_img.pes_palette), 4):
            palette_data += self.pes_img.pes_palette[j : j + 3]
        return palette_data

    def __pes_trns_to_alpha(self):
        trns_data = bytearray()
        for j in range(3, len(self.pes_img.pes_palette), 4):
            trns_data += self.pes_img.pes_palette[j : j + 1]
        #print(trns_data)
        trns_data = self.__disable_alpha(trns_data)
        #print(trns_data)
        return trns_data

    def __pes_px_to_idat(self):
        step = self.pes_img.width
        if step == 32:
            step = int(step / 2)
        idat_uncompress = bytearray()
        for j in range(0, len(self.pes_img.pes_idat), step):
            idat_uncompress += self.separator + self.pes_img.pes_idat[j : j + step]
        return bytearray(zlib.compress(idat_uncompress))

    def __disable_alpha(self,trns_data):
        for i in range(0,len(trns_data),1): #Solo toma los bytes de transparencia
            value = trns_data[i]*2
            if value >= 256: #Si el valor es (mayor o igual a 256) se resta 1 al valor
                value = value-1
            elif value <= 0: #Si no el valor es (menor o igual al 0) se queda en 0
                value = 0
            trns_data[i] = value
        return trns_data


class PNG:
    PNG_SIGNATURE = bytearray([137, 80, 78, 71, 13, 10, 26, 10])
    IHDR_LENGTH = bytearray((13).to_bytes(4, byteorder='big', signed=False))
    IHDR = bytearray([73,72,68,82])
    PLTE = bytearray([80,76,84,69])
    TRNS = bytearray([116,82,78,83])
    IDAT = bytearray([73,68,65,84])
    IEND_LENGTH = bytearray(4)
    IEND = bytearray([73,69,78,68])

class PNG_TO_TEX:
    plte = bytearray()
    trns = bytearray()
    idat = bytearray()
    width = 0
    height = 0
    size = 0
    bpp = 8
    color_type = 3
    magic_number = bytearray([0x94,0x72,0x85,0x29])   

    def __init__(self):
        self.pes_idat = bytearray()
        self.pes_palette = bytearray()
    
    def from_png(self, file_png:bytearray):
        self.png = file_png
        self.read_ihdr()
        self.read_plte_trns()
        self.merge_trns_plte()
        self.bgr_to_bgri()
        self.read_idat()
        self.idat_to_pes_px()
        
    def read_ihdr(self):
        ihdr_start = self.png.find(PNG.IHDR) # we need to move 4 bytes from the identifier
        if ihdr_start == -1:
            raise TypeError("Not a valid PNG image")
        ihdr_start+=4
        ihdr_lenght = int.from_bytes(self.png[ihdr_start - 8 : ihdr_start - 4],'big', signed=False)
        ihdr = self.png[ihdr_start : ihdr_start + ihdr_lenght]
        self.width = int.from_bytes(ihdr[:4],'big',signed=False)
        self.height = int.from_bytes(ihdr[4:8],'big',signed=False)
        
        if self.bpp != ihdr[8] and self.color_type != ihdr[9]:
            raise ValueError()

    def read_plte_trns(self):
        plte_start = self.png.find(PNG.PLTE) # we need to move 4 bytes from the identifier
        if plte_start == -1:
            raise TypeError("Not a valid PNG image")
        plte_start+=4
        
        plte_lenght = int.from_bytes(self.png[plte_start - 8 : plte_start - 4],'big', signed=False)
        self.plte = self.png[plte_start : plte_start + plte_lenght]

        trns_start = self.png.find(PNG.TRNS) # we need to move 4 bytes from the identifier
        if trns_start == -1:
            raise TypeError("Not a valid PNG image")
        trns_start+=4
        trns_lenght = int.from_bytes(self.png[trns_start - 8 : trns_start - 4],'big', signed=False)
        
        self.trns = self.png[trns_start : trns_start + trns_lenght]
        
        # Disable alpha
        for i in range(0, len(self.trns), 1):  # Solo toma los bytes de transparencia
            value = int(round(self.trns[i]/2))
            if value > 128:
                value = 128
            # Si no el valor es (menor o igual al 0) se queda en 0
            elif value <= 0:
                value = 0
            self.trns[i] = value

    def merge_trns_plte(self):
        for x in range(len(self.trns)): 
            self.pes_palette += self.plte[3*x:3*x+3]+self.trns[1*x:1*x+1] #Se intercalan los colores y transparencias (3 bytes = 1 colors, 1 byte transparencia)

    def read_idat(self):
        start_pos = 0
        idat_start_list = []
        while True:
            pos = self.png.find(PNG.IDAT,start_pos)
            if pos == -1:
                break
            idat_start_list.append(pos + 4)
            start_pos = pos + 4
        
        idat_compressed = b''
        for idat_start in idat_start_list:
            idat_lenght = int.from_bytes(self.png[idat_start - 8 : idat_start - 4],'big', signed=False)
            idat_compressed+=self.png[idat_start : idat_start + idat_lenght]
        
        self.idat = zlib.decompress(idat_compressed)


    def idat_to_pes_px(self):
        for i in range(1, len(self.idat), self.width + 1):
            self.pes_idat += self.idat[i: i + self.width]

    def bgr_to_bgri(self):
        for i in range(32,len(self.pes_palette),128):
            self.pes_palette[i:i+32], self.pes_palette[i+32:i+72] = self.pes_palette[i+32:i+72], self.pes_palette[i:i+32]
