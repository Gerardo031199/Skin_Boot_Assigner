import struct
from tkinter import messagebox, ttk, StringVar, Entry, Listbox, Menu, filedialog
from PIL import Image, ImageDraw, ImageTk
from io import BytesIO
import os
import imagequant
from file_structure import Container, unzlib_it, file_read, zlib_it, bytes_size
from file_structure.image import PESImage, PNGImage, PNG_TO_TEX
from tkinterdnd2 import DND_FILES, TkinterDnD
from file_structure.utils.common_functions import to_int
from utils.functions import resource_path

class Gui(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.appname = 'Skin Boot Assigner'
        self.version = '1.0.0'
        self.author = 'PES Indie Team'
        self.title(self.appname+' '+self.version)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self._make_file_menu()
        self.file_list = []

        self.lbox_items = Listbox(self, cursor="arrow", width=20, exportselection=False)
        self.lbox_items.grid(column=0, row=0, rowspan=2, padx=10, pady=10, sticky="NS")
        self.lbox_items.bind("<<ListboxSelect>>", lambda event: self.get_item_info())
        self.lbox_items.drop_target_register(DND_FILES)
        self.lbox_items.dnd_bind('<<Drop>>', self.drop)
        
        self.background_img = Image.new(mode="RGBA", size=(256, 256), color=(240, 240, 240))
                
        draw = ImageDraw.Draw(self.background_img)  
        draw.rectangle((0, 0, 255, 255), outline=(190, 190, 190))
        
        self.imgtk = ImageTk.PhotoImage(self.background_img)
        self.label_img = ttk.Label(self, image=self.imgtk)
        self.label_img.grid(column=1, row=0, columnspan=2, padx=10, pady=10, sticky="WE")

        self.btn_import = ttk.Button(
            self, 
            text="Import Texture", 
            command = lambda: self.import_boot_texture(),
            state='disable',
        )
        self.btn_import.grid(column=1, row=1, padx=10, pady=10, sticky="WE")  

        self.btn_fix = ttk.Button(
            self, 
            text="Fix UV", 
            command= 
            lambda : self.on_click_on_fix_uv_btn(
                self.file_list[
                    self.lbox_items.curselection()[0]
                ]
            ),
            state='disable'
        )
        self.btn_fix.grid(column=2, row=1, padx=10, pady=10, sticky="WE")
        
        self.input_files = Entry(self,background="#f0f0f0", state="readonly")
        self.input_files.grid(column=0, row=2, columnspan=3, sticky="WE")
    
    def _make_file_menu(self):
        self.my_menu=Menu(self)
        self.config(menu=self.my_menu)
        self.file_menu = Menu(self.my_menu, tearoff=0)
        self.edit_menu = Menu(self.my_menu, tearoff=0)
        self.help_menu = Menu(self.my_menu, tearoff=0)

        self.my_menu.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open folder", command=lambda : self.open_folder())
        self.file_menu.add_command(label="Exit", command= lambda : self.destroy())

        self.my_menu.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Clear file listbox", command=lambda : self.clear_listbox(), state="disabled")
        self.edit_menu.add_command(label="Fix all files", command=lambda : self.batch_process(), state="disabled")

        self.my_menu.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Manual", command=None)
        self.help_menu.add_command(label="About", command=None)

    def open_folder(self):
        folder = filedialog.askdirectory(title="Select folder", initialdir=".", parent=self)
        if folder == '':
            return 0

        for file in os.listdir(folder):
            if (file.endswith('.bin') or file.endswith('.str')) and folder+'/'+file not in self.file_list:
                self.file_list.append(folder+'/'+file)
        self.update_listbox()
        self.update_file_menu(True)

    def batch_process(self):
        for file in self.file_list:
            self.on_click_on_fix_uv_btn(file)
        messagebox.showinfo(title=self.appname, message='All files fixed! :)')

    def update_file_menu(self, flag):
        if flag:
            self.edit_menu.entryconfig("Clear file listbox", state="normal")
            self.edit_menu.entryconfig("Fix all files", state="normal")
        else:
            self.edit_menu.entryconfig("Clear file listbox", state="disabled")
            self.edit_menu.entryconfig("Fix all files", state="disabled")

    def update_listbox(self):
        self.lbox_items.delete(0, 'end')
        self.lbox_items.insert("end",* [os.path.basename(file) for file in self.file_list])

    def clear_listbox(self):
        self.lbox_items.delete(0, 'end')
        self.file_list = []

        self.input_files['state'] = "normal"
        self.input_files.delete(0, 'end')
        self.input_files['state'] = "readonly"

        self.btn_import['state'] = "disabled"
        self.btn_fix['state'] = "disabled"

        self.imgtk = ImageTk.PhotoImage(self.background_img)
        self.label_img.configure(image=self.imgtk)

        self.update_file_menu(False)


    def preview(self, IMG):
        self.img = Image.open(BytesIO(IMG))
        self.img1 = self.img.resize((256,256))

        self.imgtk = ImageTk.PhotoImage(self.img1)
            
        self.label_img.configure(image=self.imgtk)

    def get_container(self, unzlibed_file:bytearray):
        return Container(unzlibed_file)

    def is_hair(self, list_of_files:list):
        if len(list_of_files) == 3:
            return PESImage.PES_IMAGE_SIGNATURE == list_of_files[1][:4]
        else:
            return False

    def get_pes_texture(self, file_location:str):
        bin_file = file_read(file_location)
        decompress_bin_file = unzlib_it(bin_file[32:])
        return self.get_container(decompress_bin_file).files[1] if self.is_hair(self.get_container(decompress_bin_file).files) else self.get_container(decompress_bin_file).files[-1]

    def drop(self, event:TkinterDnD.DnDEvent):
        file_path_returneds = list(self.tk.splitlist(event.data))
        for file in file_path_returneds:
            if file not in self.file_list:
                self.file_list.append(file)
        self.update_listbox()
        self.update_file_menu(True)

    def get_item_info(self):
        if self.lbox_items.curselection() != ():
            item_id = self.lbox_items.curselection()[0]
            self.set_item_info(item_id)

    def set_item_info(self, item_id:int):
        file_path = self.file_list[item_id]

        path_bn_str = StringVar()

        path_bn_str.set(file_path)
            
        self.input_files.configure(textvariable=path_bn_str)

        pes_image = PESImage()
        pes_image.from_bytes(self.get_pes_texture(file_path))
        pes_image.bgr_to_bgri()
        
        png_image = PNGImage()
        png_image.png_from_pes_img(pes_image)

        self.preview(png_image.png)

        self.btn_import['state'] = "NORMAL"
        self.btn_fix['state'] = "NORMAL"

    def ps2_mdl_write_uv_list(self, mdl:BytesIO, uv_list:list, valid_textures_list:list):
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
        #vertex_factor = 0.001953
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
                    v,t = round(uv_list[vertex_count + j][0]/factor_uv), round((1 - uv_list[vertex_count + j][1]) / factor_uv)
                    mdl.write(struct.pack("<h", v))
                    mdl.write(struct.pack("<h",t))
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

    def ps2_mdl_read_uv_list(self, mdl:BytesIO, valid_textures_list:list):

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

        i = 0
        vertex_in_part_offset = 88
        uvlist = []
        factor_uv = 0.000244
        while i < total_parts:
            #print("part ",i, " offset: ", part_start_offset)
            mdl.seek(part_start_offset,0)
            part_size = struct.unpack("<I", mdl.read(4))[0]
            mdl.read(4)
            part_info_start = struct.unpack("<I", mdl.read(4))[0]
            mdl.seek(part_start_offset+52,0)
            txs_id =  struct.unpack("<I", mdl.read(4))[0]
            #print("this part use texture id: ", txs_id)
            #print(mdl.tell())
            
            if txs_id in valid_textures_indexes:
                mdl.seek(part_start_offset + vertex_in_part_offset + part_info_start,0)
                vertex_in_piece = struct.unpack("<H", mdl.read(2))[0]
                #print(vertex_in_piece)
                mdl.seek(part_start_offset + part_info_start + 96, 0)
                mdl.read(4)
                mdl.read(vertex_in_piece * 6)
                if vertex_in_piece % 2 != 0:
                    mdl.read(2)
                mdl.read(4)
                mdl.read(vertex_in_piece * 6)
                if vertex_in_piece % 2 != 0:
                    mdl.read(2)
                mdl.read(4)
                # lectura de uv
                j = 0
                while j < vertex_in_piece:
                    u, v = struct.unpack("<hh", mdl.read(4))
                    uvlist.append((u * factor_uv, 1 - (v * factor_uv)))
                    j += 1
            part_start_offset += part_size
            i += 1
        return uvlist

    def on_click_on_fix_uv_btn(self, file_path:str):
        bin_file = file_read(file_path)
        bin_header = bin_file[:32]
        decompress_bin_file = unzlib_it(bin_file[32:])
        file_ctn = self.get_container(decompress_bin_file)

        valid_textures_list = [0x64, 0x6F, 0x72]

        mdl = BytesIO(file_ctn.files[0])
        hair_texture_bytes = file_ctn.files[1]

        # empezamos la correccion de la imagen
        default_boot_texture = Image.open(resource_path('resource.png'))

        hair_image = self.get_image_from_pes_bytes(hair_texture_bytes)
        hair_image = hair_image.resize((128, 64))
        default_boot_texture.paste(hair_image)

        ############
        uvlist = self.ps2_mdl_read_uv_list(mdl, valid_textures_list)
        uvlist = self.multiply_uv(uvlist, 1, 0.5)
        uvlist = self.add_uv(uvlist, 0, 0.5)
        # importamos el uv modificado al bytesio y lo recibimos en bytes para luego escribirlo
        mdl_bytes = self.ps2_mdl_write_uv_list(mdl, uvlist, valid_textures_list)

        offset_mdl =  to_int(decompress_bin_file[8:12])
        offset_tex1 = to_int(decompress_bin_file[12:16])
        offset_tex2 = to_int(decompress_bin_file[16:20])

        # escribimos los bytes del mdl en el archivo descomprimido
        decompress_bin_file[offset_mdl: offset_tex1] = mdl_bytes
        # importamos la primer imagen
        decompress_bin_file = self.import_img_to_bin(decompress_bin_file, default_boot_texture, 256, offset_tex1, False, True, True)

        #redimensionamos la primer imagen e importamos solos los bytes de los pixeles
        default_boot_texture_2 = default_boot_texture.resize((64,64))
        decompress_bin_file = self.import_img_to_bin(decompress_bin_file, default_boot_texture_2, 256, offset_tex2, False, False, True)

        # Comprimimos nuestro archivo y obtenemos los datos necesarios
        bin_data_zlib = zlib_it(decompress_bin_file, 9)
        size_compress = bytes_size(bin_data_zlib)
        size_uncompress = bytes_size(decompress_bin_file)
        bin_header[4:8] = size_compress
        bin_header[8:12] = size_uncompress

        # escribimos los datos en memoria a el archivo
        with open(file_path, "wb") as f:
            f.write(bin_header)
            f.write(bin_data_zlib)

        # actualizamos la gui
        
        self.lbox_items.select_set(self.file_list.index(file_path))
        self.lbox_items.event_generate('<<ListboxSelect>>')
    
    def multiply_uv(self, uv_list:list, u_factor:float, v_factor:float):
        return [(uv[0] * u_factor, uv[1] * v_factor) for uv in uv_list]
        
    def add_uv(self, uv_list:list, u_factor:float, v_factor:float):
        return [(uv[0] + u_factor, uv[1] + v_factor) for uv in uv_list]

    def minus_uv(self, uv_list:list, u_factor:float, v_factor:float):
        return [(uv[0] - u_factor, uv[1] - v_factor) for uv in uv_list]

    def import_boot_texture(self):
        filetypes = [
            ("Png Image", ".png"),
            ('All files', '*.*'),
        ]

        filename = filedialog.askopenfilename(
            title=f'{self.appname} Select your boot texture',
            initialdir='.',
            filetypes=filetypes)
        if filename == "":
            return 0
        
        # we create an empty image first
        boot_canvas = Image.new(mode="RGBA", size=(128, 128), color=(255, 255, 255,0))
        #boot_canvas.save("./test/bcanvas.png")
        new_boot_texture = Image.open(filename)
        
        # check if its a valid boot texture
        if new_boot_texture.size != (128,64):
            messagebox.showerror(title=self.appname, message="Texture size error, must be 128x64")
            return 0
        new_boot_texture = new_boot_texture.convert("RGBA")

        item_id = self.lbox_items.curselection()[0]
        hair_file_path = self.file_list[item_id]

        # Reading file...

        bin_file = file_read(hair_file_path)
        
        bin_header = bin_file[:32]

        decompress_bin_file = unzlib_it(bin_file[32:])

        file_ctn = self.get_container(decompress_bin_file)
        
        hair_texture_bytes = file_ctn.files[1]

        # converting pes image buffer into python image
        hair_image = self.get_image_from_pes_bytes(hair_texture_bytes)

        # cropping only the hair texture
        hair_image = hair_image.crop((0, 0, 128, 64))
        #hair_texture.save("./test/hair_txs.png")
        
        # and then merging the new boot texture and hair texture into the canvas
        
        boot_canvas.paste(hair_image, (0,0))
        #boot_canvas.save("./test/bcanvas_with_hair.png")
        boot_canvas.paste(new_boot_texture, (0,64))
        #boot_canvas.save("./test/bcanvas_with_boot.png")


        offset_tex1 = to_int(decompress_bin_file[12:16])
        offset_tex2 = to_int(decompress_bin_file[16:20])

        decompress_bin_file = self.import_img_to_bin(decompress_bin_file, boot_canvas, 256, offset_tex1, False, True, True)
        #print("textura 1 importada!")
   
        boot_canvas2 = boot_canvas.resize((64,64))

        decompress_bin_file = self.import_img_to_bin(decompress_bin_file, boot_canvas2, 256, offset_tex2, False, False, True)
        #print("Txtura 2 importda!!")
        #return 0
        bin_data_zlib = zlib_it(decompress_bin_file, 9)
        
        size_compress = bytes_size(bin_data_zlib)

        size_uncompress = bytes_size(decompress_bin_file)

        bin_header[4:8] = size_compress

        bin_header[8:12] = size_uncompress

        with open(hair_file_path, "wb") as f:
            f.write(bin_header)
            f.write(bin_data_zlib)

        messagebox.showinfo(title=self.appname, message="Texture boot imported!")
        
        self.lbox_items.select_set(self.file_list.index(hair_file_path))
        self.lbox_items.event_generate('<<ListboxSelect>>')

    def get_image_from_pes_bytes(self, pes_bytes:bytearray):
        pes_image = PESImage()
        pes_image.from_bytes(pes_bytes)
        pes_image.bgr_to_bgri()
        png_image = PNGImage()
        png_image.png_from_pes_img(pes_image)
        return Image.open(BytesIO(png_image.png))

    def img_to_bytes(self, img:Image.Image):
        output = BytesIO()
        img.save(output,'PNG')
        output_content = bytearray(output.getvalue())
        output.close()
        return output_content

    def index_img(self, img:Image.Image, colors:int):
        return imagequant.quantize_pil_image(img, dithering_level=1.0, max_colors=colors)


    def import_img_to_bin(self, data:bytearray, img:Image.Image, colors:int, offset:int, is_indexed:bool, import_palette:bool, import_pixel:bool):
        #return 0

        txs_size = to_int(data[offset+8:offset+12])

        pixel_offset = to_int(data[offset+16:offset+18])

        palette_offset = to_int(data[offset+18:offset+20])
        
        width = to_int(data[offset+20:offset+22])
        
        heigth = to_int(data[offset+22:offset+24])

        bitmap = to_int(data[offset+48:offset+50])

        if not is_indexed:
            img = self.index_img(img, colors)
        
        img_bytes = self.img_to_bytes(img)

        pes_img1 = PNG_TO_TEX()
        pes_img1.from_png(img_bytes)

        if pes_img1.width != width and pes_img1.height != heigth:
            messagebox.showerror(title=self.appname, message="The sizes is not valid, image not imported")
            return data
        
        if import_palette:
            data[offset + palette_offset : pixel_offset + offset] = pes_img1.pes_palette
        
        if import_pixel:
            data[offset + pixel_offset : txs_size + offset] = pes_img1.pes_idat

        if bitmap != 0:
            img2 = img.resize((int(width/2),int(heigth/2)))
        
            img2_bytes = self.img_to_bytes(img2)

            pes_img2 = PNG_TO_TEX()
            pes_img2.from_png(img2_bytes)

            data[offset + txs_size : offset + len(pes_img2.pes_idat)] = pes_img2.pes_idat

        return data

    def start(self):
        self.mainloop()

def main():
    Gui().start()

if __name__ == '__main__':
    main()
