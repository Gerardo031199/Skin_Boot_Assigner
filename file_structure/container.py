from .utils.common_functions import to_int


class Container:

    def __init__(self,container_bytes: bytearray):
        self.container_bytes = container_bytes
        self.total_files = to_int(container_bytes[:4])
        self.idx_tbl_offset = to_int(container_bytes[4:8])
        self.load_files_table()
        self.load_files()
    
    def load_files_table(self):
        """
        Load the start offset for each file in the container
        """
        self.files_offset = []
        for i in range(self.total_files):
            offset = to_int(self.container_bytes[
                self.idx_tbl_offset + i * 4 : self.idx_tbl_offset + i * 4 + 4
                ])
            self.files_offset.append(offset)

    def load_files(self):
        """
        Load each file into a list
        """
        self.files = []
        for i in range(self.total_files):
            if i == self.total_files -1:
                offset = bytearray(self.container_bytes[self.files_offset[i] : ])
            else:
                offset = bytearray(self.container_bytes[
                    self.files_offset[i] : self.files_offset[i + 1]
                    ])
            self.files.append(offset)
