class PPU:
    def __init__(self, mmu, cpu):
        self.mmu = mmu
        self.cpu = cpu

        # 2d array of pixels
        self.framebuffer = [[(255, 255, 255)] * 160 for _ in range(144)]

        # Gameboy colors
        self.colors = [
            (255, 255, 255), # White
            (192, 192, 192), # Light Gray
            (96, 96, 96),   # Dark Gray
            (0, 0, 0),       # Black
        ]

        # PPU state
        self.dots = 0
        self.mode = 2 # Start in OAM Scan mode

    def step(self, cycles):
        lcdc = self.mmu.read_byte(0xFF40)
        if not (lcdc >> 7) & 1:
            # LCD is disabled
            self.mmu.write_byte(0xFF44, 0)
            self.dots = 0
            self.mode = 0
            return

        self.dots += cycles

        # LY is the current horizontal line being drawn
        ly = self.mmu.read_byte(0xFF44)

        if self.mode == 2: # OAM Scan
            if self.dots >= 80:
                self.dots = 0
                self.mode = 3
        elif self.mode == 3: # Drawing
            if self.dots >= 172:
                self.dots = 0
                self.mode = 0
                self._render_scanline(ly)
        elif self.mode == 0: # H-Blank
            if self.dots >= 204:
                self.dots = 0
                ly += 1
                if ly <= 144:
                    self.mmu.write_byte(0xFF44, ly)
                if ly == 144:
                    self.mode = 1
                    # Trigger V-Blank interrupt
                    self.cpu.ime = 1 # For now, just enable interrupts, need to implement interrupt system
                    self.mmu.write_byte(0xFF0F, self.mmu.read_byte(0xFF0F) | 1)
                else:
                    self.mode = 2
        elif self.mode == 1: # V-Blank
            if self.dots >= 456:
                self.dots = 0
                ly += 1
                if ly <= 153:
                    self.mmu.write_byte(0xFF44, ly)
                if ly > 153:
                    self.mode = 2
                    self.mmu.write_byte(0xFF44, 0)

    def _render_scanline(self, ly):
        lcdc = self.mmu.read_byte(0xFF40)
        
        # Is background enabled?
        if (lcdc >> 0) & 1:
            self._render_background(ly, lcdc)

        # Are sprites enabled? (Not implemented yet)
        # if (lcdc >> 1) & 1:
        #     self._render_sprites(ly, lcdc)

    def _render_background(self, ly, lcdc):
        scy = self.mmu.read_byte(0xFF42)
        scx = self.mmu.read_byte(0xFF43)
        bgp = self.mmu.read_byte(0xFF47)

        tile_map_addr = 0x9C00 if (lcdc >> 3) & 1 else 0x9800
        tile_data_addr = 0x8000 if (lcdc >> 4) & 1 else 0x8800
        
        y_in_map = (ly + scy) & 0xFF
        
        for x in range(160):
            x_in_map = (x + scx) & 0xFF
            
            tile_map_x = x_in_map // 8
            tile_map_y = y_in_map // 8
            
            tile_id_addr = tile_map_addr + tile_map_y * 32 + tile_map_x
            tile_id = self.mmu.read_byte(tile_id_addr)
            
            if tile_data_addr == 0x8800: #signed tiles
                tile_data_start = tile_data_addr + ((tile_id) * 16)
            else: #unsigned tiles
                tile_data_start = tile_data_addr + (tile_id * 16)

            y_in_tile = y_in_map % 8
            
            byte1 = self.mmu.read_byte(tile_data_start + y_in_tile * 2)
            byte2 = self.mmu.read_byte(tile_data_start + y_in_tile * 2 + 1)
            
            x_in_tile = x_in_map % 8
            
            bit = 7 - x_in_tile
            color_id = ((byte2 >> bit) & 1) << 1 | ((byte1 >> bit) & 1)
            
            # Map color id to actual color using BGP
            palette_color = (bgp >> (color_id * 2)) & 0b11
            
            self.framebuffer[ly][x] = self.colors[palette_color]