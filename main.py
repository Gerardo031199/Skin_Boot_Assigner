import struct
from tkinter import messagebox, ttk, StringVar, Entry, Listbox, Menu, filedialog
from PIL import Image, ImageDraw, ImageTk
from io import BytesIO
import os
import imagequant

from file_structure import Container, unzlib_it, file_read, zlib_it, bytes_size, openBaseModel
from file_structure.image import PESImage, PNGImage, PNG_TO_TEX

# Fix for tkinterdnd2
from tkinterdnd2 import DND_FILES, Tk
from PyInstaller.utils.hooks import collect_data_files, eval_statement
#from PyInstaller.utils.hooks import collect_data_files, eval_statement

from tkinterdnd2 import DND_FILES, TkinterDnD
from file_structure.utils.common_functions import to_int
from utils.functions import resource_path

datas = collect_data_files('tkinterdnd2')
#datas = collect_data_files('tkinterdnd2')

class Gui(Tk):
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

        self.btn_import = ttk.Button(self, text="Import Texture", command=None, state='disable')
        self.btn_import.grid(column=1, row=1, padx=10, pady=10, sticky="WE")  

        self.btn_fix = ttk.Button(self, text="Fix UV", command= lambda : self.fix_uv(self.file_list[self.lbox_items.curselection()[0]]), state='disable')
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
        self.file_menu.add_command(label="Save", state='disabled',command=None)
        self.file_menu.add_command(label="Save as...", state='disabled', command=None)
        self.file_menu.add_command(label="Exit", command= None)

        self.my_menu.add_cascade(label="Edit", menu=self.edit_menu)
        self.edit_menu.add_command(label="Clear file listbox", command=lambda : self.clear_listbox(), state="disabled")
        self.edit_menu.add_command(label="Fix all files", command=lambda : self.batch_process(), state="disabled")
        #self.edit_submenu = Menu(self.my_menu, tearoff=0)
        # Dinamically loading game versions as sub menu
        #for i in range(len(self.my_config.games_config)):
        #    self.edit_submenu.add_command(label=self.my_config.games_config[i],command= lambda i=i: self.change_config(self.my_config.filelist[i]))
        #self.edit_menu.add_cascade(label="Game Version", menu=self.edit_submenu)

        self.my_menu.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="Manual", command=None)
        self.help_menu.add_command(label="About", command=None)

    def open_folder(self):
        folder = filedialog.askdirectory(title="Select folder", initialdir=".", parent=self)
        if folder == '':
            return 0
        #print(folder)

        for file in os.listdir(folder):
            if (file.endswith('.bin') or file.endswith('.str')) and folder+'/'+file not in self.file_list:
                self.file_list.append(folder+'/'+file)
        self.update_listbox()
        self.update_file_menu(True)

    def batch_process(self):
        for file in self.file_list:
            self.fix_uv(file)
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

    def drop(self, event):
        file_path_returneds = list(self.tk.splitlist(event.data))

        #paths = [os.path.basename(w) 
        for file in file_path_returneds:
            if file not in self.file_list:
                self.file_list.append(file)
        self.update_listbox()
        self.update_file_menu(True)

    def get_item_info(self):
        if self.lbox_items.curselection() != ():
            item_id = self.lbox_items.curselection()[0]
            self.set_item_info(item_id)

    def set_item_info(self, item_id):
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
    
    def fix_uv(self, file_path):
        pes_image = PESImage()
        pes_image.from_bytes(self.get_pes_texture(file_path))
        pes_image.bgr_to_bgri()

        png_image = PNGImage()
        png_image.png_from_pes_img(pes_image)

        img = Image.open(resource_path('resource.png'))
        img1_copy = img.copy() 

        output0 = BytesIO()
        img_bytes = Image.open(BytesIO(png_image.png))
        img_bytes = img_bytes.resize((128,64))
        #new_img.save('file_128x64.png')
        img_bytes.save(output0, 'PNG') 

        img2_copy = img_bytes.copy() 
        img1_copy.paste(img2_copy,(0, 0)) 
        #resource_img_copy.save('pasted2.png') 
        
        output1 = BytesIO()
        new_img1 = imagequant.quantize_pil_image(img1_copy, dithering_level=1.0, max_colors=256)
        new_img1.save(output1, 'PNG') 
        output1_content = bytearray(output1.getvalue())
        #new_img1.save("128_x_128.png")

        output2 = BytesIO()
        new_img2 = new_img1.resize((64,64))
        new_img2 = imagequant.quantize_pil_image(new_img2, dithering_level=1.0, max_colors=256)
        new_img2.save(output2, 'PNG') 
        output2_content = bytearray(output2.getvalue())
        #new_img2.save("64_x_64.png")
        bin_file = file_read(file_path)
        
        bin_header = bin_file[:32]

        decompress_bin_file = unzlib_it(bin_file[32:])

        file_temp = BytesIO()
        file_temp.write(decompress_bin_file)

        file_ctn = self.get_container(decompress_bin_file)
        
        valid_textures_list = [0x64, 0x6F, 0x72]
        
        mdl = BytesIO(file_ctn.files[0])
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
                for j in range(vertex_in_piece):
                    u,v = struct.unpack("<hh", mdl.read(4))
                    uvlist.append((u * factor_uv, 1 - v * factor_uv * 0.5))
            part_start_offset += part_size
            i += 1

        bin_data_uncompress = bytearray(openBaseModel(file_temp, uvlist))
        
        offset_tex1 =  to_int(bin_data_uncompress[12:14])
        offset_tex2 =  to_int(bin_data_uncompress[16:18])

        pes_img1 = PNG_TO_TEX()
        pes_img1.from_png(output1_content)
        
        pes_img2 = PNG_TO_TEX()
        pes_img2.from_png(output2_content)

        bin_data_uncompress[offset_tex1+128:offset_tex2] = pes_img1.pes_palette + pes_img1.pes_idat
        
        bin_data_uncompress[offset_tex2+128:] = pes_img2.pes_idat

        bin_data_zlib = zlib_it(bin_data_uncompress, 9)
        
        size_compress = bytes_size(bin_data_zlib)

        size_uncompress = bytes_size(bin_data_uncompress)

        bin_header[4:8] = size_compress

        bin_header[8:12] = size_uncompress

        with open(file_path, "wb") as f:
            f.write(bin_header)
            f.write(bin_data_zlib)

    def start(self):
        self.mainloop()

def main():
    Gui().start()

if __name__ == '__main__':
    main()
