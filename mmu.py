class MMU:
    def __init__(self):
        self.memory = bytearray(65536) # 64 * 1024

    def read_byte(self, address):
        if address == 0xFF00: # JOYP (Joypad)
            #need to implement
            return 0xFF
        elif address == 0xFF04: # DIV (Divider Register)
            #need to implement
            return 0
        elif address == 0xFF0F: # IF (Interrupt Flag)
            #need to implement
            return self.memory[address]
        elif 0xFF40 <= address <= 0xFF4B: # PPU registers
            #need to implement
            return self.memory[address]

        return self.memory[address]

    def write_byte(self, address, value):
        if address == 0xFF00: # JOYP (Joypad)
            # only bits 4 and 5 are writable (direction/action buttons select)
            self.memory[address] = (self.memory[address] & 0xCF) | (value & 0x30)
            return
        elif address == 0xFF04: # DIV (Divider Register)
            # writing to DIV resets it to 0 (need to verify)
            self.memory[address] = 0
            return
        elif address == 0xFF0F: # IF (Interrupt Flag)
            self.memory[address] = value | 0b11100000 # Lower 5 bits are writable
            return
        elif address == 0xFF44: # LY (LCD Y-coordinate) is read-only for CPU
            #modifying on for testing purposing
            self.memory[address] = value
            return
        elif 0xFF40 <= address <= 0xFF4B: # PPU registers
            self.memory[address] = value
            return

        if address < 0x8000:
            #should be restricted
            pass
        self.memory[address] = value

    def load_rom(self, rom_path):
        try:
            with open(rom_path, 'rb') as f:
                rom_data = f.read()
                self.memory[0x0000:len(rom_data)] = rom_data
            print(f"ROM '{rom_path}' loaded successfully.")
        except FileNotFoundError:
            print(f"Error: ROM file not found at '{rom_path}'")
        except Exception as e:
            print(f"An error occurred while loading the ROM: {e}")