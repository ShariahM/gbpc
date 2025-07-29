class CPU:
    def __init__(self, mmu):
        self.mmu = mmu

        # 8-bit registers
        self.a = 0x01
        self.b = 0x00
        self.c = 0x13
        self.d = 0x00
        self.e = 0xD8
        self.h = 0x01
        self.l = 0x4D
        
        # F (Flags) register
        self.f = 0xB0

        # 16-bit registers
        self.pc = 0x0100
        self.sp = 0xFFFE

        # Interrupt Master Enable Flag
        self.ime = 0

        self._create_opcode_map()
        self._create_cbcode_map()

    # --- 16-bit register access ---
    def _get_bc(self):
        return (self.b << 8) | self.c

    def _set_bc(self, value):
        self.b = (value >> 8) & 0xFF
        self.c = value & 0xFF

    def _get_de(self):
        return (self.d << 8) | self.e

    def _set_de(self, value):
        self.d = (value >> 8) & 0xFF
        self.e = value & 0xFF

    def _get_hl(self):
        return (self.h << 8) | self.l

    def _set_hl(self, value):
        self.h = (value >> 8) & 0xFF
        self.l = value & 0xFF

    # --- Flag management ---
    def _get_flag_z(self):
        return (self.f >> 7) & 1

    def _set_flag_z(self, value):
        self.f = (self.f & 0x7F) | (value << 7)

    def _get_flag_n(self):
        return (self.f >> 6) & 1

    def _set_flag_n(self, value):
        self.f = (self.f & 0xBF) | (value << 6)

    def _get_flag_h(self):
        return (self.f >> 5) & 1

    def _set_flag_h(self, value):
        self.f = (self.f & 0xDF) | (value << 5)

    def _get_flag_c(self):
        return (self.f >> 4) & 1

    def _set_flag_c(self, value):
        self.f = (self.f & 0xEF) | (value << 4)

    def step(self):
        opcode = self.mmu.read_byte(self.pc)
        self.pc += 1
        instruction = self.opcodes.get(opcode)
        if instruction:
            print(hex(opcode))
            return instruction()
        else:
            print(opcode)
            print(f"Unknown opcode: {hex(opcode)}")
            exit(1)
            return 4

    def _read_next_byte(self):
        val = self.mmu.read_byte(self.pc)
        self.pc += 1
        return val

    def _read_next_word(self):
        low = self._read_next_byte()
        high = self._read_next_byte()
        return (high << 8) | low

    def _push_word(self, value):
        self.sp -= 1
        self.mmu.write_byte(self.sp, (value >> 8) & 0xFF)
        self.sp -= 1
        self.mmu.write_byte(self.sp, value & 0xFF)

    def _pop_word(self):
        low = self.mmu.read_byte(self.sp)
        self.sp += 1
        high = self.mmu.read_byte(self.sp)
        self.sp += 1
        return (high << 8) | low

    def _inc(self, value):
        result = (value + 1) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h((value & 0x0F) == 0x0F)
        return result

    def _dec(self, value):
        result = (value - 1) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(1)
        self._set_flag_h((value & 0x0F) == 0x00)
        return result
    
    def _jr(self, flag):
        offset = self._read_next_byte()
        if offset >= 0x80:
            offset -= 0x100 
        if flag == 1:
            self.pc += offset
            return 12
        elif flag == 0:
            return 8

    def _ccf(self):
        self._set_flag_c(1 - self._get_flag_c())
        self._set_flag_n(0)
        self._set_flag_h(0)
        return 4

    def _rlc(self, value):
        carry = (value >> 7) & 1
        result = ((value << 1) | carry) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(carry)
        return result

    def _rrc(self, value):
        carry = value & 1
        result = ((value >> 1) | (carry << 7)) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(carry)
        return result

    def _rl(self, value):
        carry = self._get_flag_c()
        new_carry = (value >> 7) & 1
        result = ((value << 1) | carry) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(new_carry)
        return result

    def _rr(self, value):
        carry = self._get_flag_c()
        new_carry = value & 1
        result = ((value >> 1) | (carry << 7)) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(new_carry)
        return result

    def _sla(self, value):
        carry = (value >> 7) & 1
        result = (value << 1) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(carry)
        return result

    def _sra(self, value):
        carry = value & 1
        msb = value & 0x80
        result = (value >> 1) | msb
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(carry)
        return result

    def _srl(self, value):
        carry = value & 1
        result = (value >> 1) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(carry)
        return result

    def _swap(self, value):
        result = ((value << 4) | (value >> 4)) & 0xFF
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return result

    def _bit(self, bit_index, value):
        bit_set = (value >> bit_index) & 1
        self._set_flag_z(bit_set == 0)
        self._set_flag_n(0)
        self._set_flag_h(1)

    def _res(self, bit, value):
        mask = ~(1 << bit) & 0xFF
        result = value & mask 
        return result

    def _set(self, bit, value):
        return value | (1 << bit)
    
    
    def _add(self, value):
        result = self.a + value
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (value & 0x0F) > 0x0F)
        self._set_flag_c(result > 0xFF)
        return result & 0xFF

    def _adc(self, value):
        carry = self._get_flag_c()
        result = self.a + value + carry
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (value & 0x0F) + carry > 0x0F)
        self._set_flag_c(result > 0xFF)
        return result & 0xFF

    def _sub(self, value):
        result = self.a - value
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(1)
        self._set_flag_h((self.a & 0x0F) < (value & 0x0F))
        self._set_flag_c(self.a < value)
        return result & 0xFF

    def _sbc(self, value):
        carry = self._get_flag_c()
        result = self.a - value - carry
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(1)
        self._set_flag_h(((self.a & 0x0F) - (value & 0x0F) - carry) < 0)
        self._set_flag_c(result < 0)
        return result & 0xFF

    def _cp(self, value):
        result = self.a - value
        self._set_flag_z(result == 0)
        self._set_flag_n(1)
        self._set_flag_h((self.a & 0x0F) < (value & 0x0F))
        self._set_flag_c(self.a < value)

    def _set_flags_alu(self, result):
        self._set_flag_z(result == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)

    def _create_cbcode_map(self):
        self.cbcodes = {
            0x00: self.cb_0x00, 0x01: self.cb_0x01, 0x02: self.cb_0x02, 0x03: self.cb_0x03,
            0x04: self.cb_0x04, 0x05: self.cb_0x05, 0x06: self.cb_0x06, 0x07: self.cb_0x07,
            0x08: self.cb_0x08, 0x09: self.cb_0x09, 0x0A: self.cb_0x0a, 0x0B: self.cb_0x0b,
            0x0C: self.cb_0x0c, 0x0D: self.cb_0x0d, 0x0E: self.cb_0x0e, 0x0F: self.cb_0x0f,

            0x10: self.cb_0x10, 0x11: self.cb_0x11, 0x12: self.cb_0x12, 0x13: self.cb_0x13,
            0x14: self.cb_0x14, 0x15: self.cb_0x15, 0x16: self.cb_0x16, 0x17: self.cb_0x17,
            0x18: self.cb_0x18, 0x19: self.cb_0x19, 0x1A: self.cb_0x1a, 0x1B: self.cb_0x1b,
            0x1C: self.cb_0x1c, 0x1D: self.cb_0x1d, 0x1E: self.cb_0x1e, 0x1F: self.cb_0x1f,

            0x20: self.cb_0x20, 0x21: self.cb_0x21, 0x22: self.cb_0x22, 0x23: self.cb_0x23,
            0x24: self.cb_0x24, 0x25: self.cb_0x25, 0x26: self.cb_0x26, 0x27: self.cb_0x27,
            0x28: self.cb_0x28, 0x29: self.cb_0x29, 0x2A: self.cb_0x2a, 0x2B: self.cb_0x2b,
            0x2C: self.cb_0x2c, 0x2D: self.cb_0x2d, 0x2E: self.cb_0x2e, 0x2F: self.cb_0x2f,

            0x30: self.cb_0x30, 0x31: self.cb_0x31, 0x32: self.cb_0x32, 0x33: self.cb_0x33,
            0x34: self.cb_0x34, 0x35: self.cb_0x35, 0x36: self.cb_0x36, 0x37: self.cb_0x37,
            0x38: self.cb_0x38, 0x39: self.cb_0x39, 0x3A: self.cb_0x3a, 0x3B: self.cb_0x3b,
            0x3C: self.cb_0x3c, 0x3D: self.cb_0x3d, 0x3E: self.cb_0x3e, 0x3F: self.cb_0x3f,

            0x40: self.cb_0x40, 0x41: self.cb_0x41, 0x42: self.cb_0x42, 0x43: self.cb_0x43,
            0x44: self.cb_0x44, 0x45: self.cb_0x45, 0x46: self.cb_0x46, 0x47: self.cb_0x47, 
            0x48: self.cb_0x48, 0x49: self.cb_0x49, 0x4A: self.cb_0x4a, 0x4B: self.cb_0x4b, 
            0x4C: self.cb_0x4c, 0x4D: self.cb_0x4d, 0x4E: self.cb_0x4e, 0x4F: self.cb_0x4f, 

            0x50: self.cb_0x50, 0x51: self.cb_0x51, 0x52: self.cb_0x52, 0x53: self.cb_0x53,
            0x54: self.cb_0x54, 0x55: self.cb_0x55, 0x56: self.cb_0x56, 0x57: self.cb_0x57,
            0x58: self.cb_0x58, 0x59: self.cb_0x59, 0x5A: self.cb_0x5a, 0x5B: self.cb_0x5b,
            0x5C: self.cb_0x5c, 0x5D: self.cb_0x5d, 0x5E: self.cb_0x5e, 0x5F: self.cb_0x5f,

            0x60: self.cb_0x60, 0x61: self.cb_0x61, 0x62: self.cb_0x62, 0x63: self.cb_0x63,
            0x64: self.cb_0x64, 0x65: self.cb_0x65, 0x66: self.cb_0x66, 0x67: self.cb_0x67,
            0x68: self.cb_0x68, 0x69: self.cb_0x69, 0x6A: self.cb_0x6a, 0x6B: self.cb_0x6b,
            0x6C: self.cb_0x6c, 0x6D: self.cb_0x6d, 0x6E: self.cb_0x6e, 0x6F: self.cb_0x6f,

            0x70: self.cb_0x70, 0x71: self.cb_0x71, 0x72: self.cb_0x72, 0x73: self.cb_0x73,
            0x74: self.cb_0x74, 0x75: self.cb_0x75, 0x76: self.cb_0x76, 0x77: self.cb_0x77,
            0x78: self.cb_0x78, 0x79: self.cb_0x79, 0x7A: self.cb_0x7a, 0x7B: self.cb_0x7b,
            0x7C: self.cb_0x7c, 0x7D: self.cb_0x7d, 0x7E: self.cb_0x7e, 0x7F: self.cb_0x7f,

            0x80: self.cb_0x80, 0x81: self.cb_0x81, 0x82: self.cb_0x82, 0x83: self.cb_0x83,
            0x84: self.cb_0x84, 0x85: self.cb_0x85, 0x86: self.cb_0x86, 0x87: self.cb_0x87,
            0x88: self.cb_0x88, 0x89: self.cb_0x89, 0x8A: self.cb_0x8a, 0x8B: self.cb_0x8b,
            0x8C: self.cb_0x8c, 0x8D: self.cb_0x8d, 0x8E: self.cb_0x8e, 0x8F: self.cb_0x8f,

            0x90: self.cb_0x90, 0x91: self.cb_0x91, 0x92: self.cb_0x92, 0x93: self.cb_0x93,
            0x94: self.cb_0x94, 0x95: self.cb_0x95, 0x96: self.cb_0x96, 0x97: self.cb_0x97,
            0x98: self.cb_0x98, 0x99: self.cb_0x99, 0x9A: self.cb_0x9a, 0x9B: self.cb_0x9b,
            0x9C: self.cb_0x9c, 0x9D: self.cb_0x9d, 0x9E: self.cb_0x9e, 0x9F: self.cb_0x9f,

            0xA0: self.cb_0xa0, 0xA1: self.cb_0xa1, 0xA2: self.cb_0xa2, 0xA3: self.cb_0xa3,
            0xA4: self.cb_0xa4, 0xA5: self.cb_0xa5, 0xA6: self.cb_0xa6, 0xA7: self.cb_0xa7,
            0xA8: self.cb_0xa8, 0xA9: self.cb_0xa9, 0xAA: self.cb_0xaa, 0xAB: self.cb_0xab,
            0xAC: self.cb_0xac, 0xAD: self.cb_0xad, 0xAE: self.cb_0xae, 0xAF: self.cb_0xaf,

            0xB0: self.cb_0xb0, 0xB1: self.cb_0xb1, 0xB2: self.cb_0xb2, 0xB3: self.cb_0xb3,
            0xB4: self.cb_0xb4, 0xB5: self.cb_0xb5, 0xB6: self.cb_0xb6, 0xB7: self.cb_0xb7,
            0xB8: self.cb_0xb8, 0xB9: self.cb_0xb9, 0xBA: self.cb_0xba, 0xBB: self.cb_0xbb,
            0xBC: self.cb_0xbc, 0xBD: self.cb_0xbd, 0xBE: self.cb_0xbe, 0xBF: self.cb_0xbf,

            0xC0: self.cb_0xc0, 0xC1: self.cb_0xc1, 0xC2: self.cb_0xc2, 0xC3: self.cb_0xc3,
            0xC4: self.cb_0xc4, 0xC5: self.cb_0xc5, 0xC6: self.cb_0xc6, 0xC7: self.cb_0xc7,
            0xC8: self.cb_0xc8, 0xC9: self.cb_0xc9, 0xCA: self.cb_0xca, 0xCB: self.cb_0xcb,
            0xCC: self.cb_0xcc, 0xCD: self.cb_0xcd, 0xCE: self.cb_0xce, 0xCF: self.cb_0xcf,

            0xD0: self.cb_0xd0, 0xD1: self.cb_0xd1, 0xD2: self.cb_0xd2, 0xD3: self.cb_0xd3,
            0xD4: self.cb_0xd4, 0xD5: self.cb_0xd5, 0xD6: self.cb_0xd6, 0xD7: self.cb_0xd7,
            0xD8: self.cb_0xd8, 0xD9: self.cb_0xd9, 0xDA: self.cb_0xda, 0xDB: self.cb_0xdb,
            0xDC: self.cb_0xdc, 0xDD: self.cb_0xdd, 0xDE: self.cb_0xde, 0xDF: self.cb_0xdf,

            0xE0: self.cb_0xe0, 0xE1: self.cb_0xe1, 0xE2: self.cb_0xe2, 0xE3: self.cb_0xe3,
            0xE4: self.cb_0xe4, 0xE5: self.cb_0xe5, 0xE6: self.cb_0xe6, 0xE7: self.cb_0xe7,
            0xE8: self.cb_0xe8, 0xE9: self.cb_0xe9, 0xEA: self.cb_0xea, 0xEB: self.cb_0xeb,
            0xEC: self.cb_0xec, 0xED: self.cb_0xed, 0xEE: self.cb_0xee, 0xEF: self.cb_0xef,

            0xF0: self.cb_0xf0, 0xF1: self.cb_0xf1, 0xF2: self.cb_0xf2, 0xF3: self.cb_0xf3,
            0xF4: self.cb_0xf4, 0xF5: self.cb_0xf5, 0xF6: self.cb_0xf6, 0xF7: self.cb_0xf7,
            0xF8: self.cb_0xf8, 0xF9: self.cb_0xf9, 0xFA: self.cb_0xfa, 0xFB: self.cb_0xfb,
            0xFC: self.cb_0xfc, 0xFD: self.cb_0xfd, 0xFE: self.cb_0xfe, 0xFF: self.cb_0xff,
        }

    def cb_0x00(self): self.b = self._rlc(self.b); return 8
    def cb_0x01(self): self.c = self._rlc(self.c); return 8
    def cb_0x02(self): self.d = self._rlc(self.d); return 8
    def cb_0x03(self): self.e = self._rlc(self.e); return 8
    def cb_0x04(self): self.h = self._rlc(self.h); return 8
    def cb_0x05(self): self.l = self._rlc(self.l); return 8
    def cb_0x06(self): self.mmu.write_byte(self._get_hl(), self._rlc(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x07(self): self.a = self._rlc(self.a); return 8

    def cb_0x08(self): self.b = self._rrc(self.b); return 8
    def cb_0x09(self): self.c = self._rrc(self.c); return 8
    def cb_0x0a(self): self.d = self._rrc(self.d); return 8
    def cb_0x0b(self): self.e = self._rrc(self.e); return 8
    def cb_0x0c(self): self.h = self._rrc(self.h); return 8
    def cb_0x0d(self): self.l = self._rrc(self.l); return 8
    def cb_0x0e(self): self.mmu.write_byte(self._get_hl(), self._rrc(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x0f(self): self.a = self._rrc(self.a); return 8

    def cb_0x10(self): self.b = self._rl(self.b); return 8
    def cb_0x11(self): self.c = self._rl(self.c); return 8
    def cb_0x12(self): self.d = self._rl(self.d); return 8
    def cb_0x13(self): self.e = self._rl(self.e); return 8
    def cb_0x14(self): self.h = self._rl(self.h); return 8
    def cb_0x15(self): self.l = self._rl(self.l); return 8
    def cb_0x16(self): self.mmu.write_byte(self._get_hl(), self._rl(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x17(self): self.a = self._rl(self.a); return 8

    def cb_0x18(self): self.b = self._rr(self.b); return 8
    def cb_0x19(self): self.c = self._rr(self.c); return 8
    def cb_0x1a(self): self.d = self._rr(self.d); return 8
    def cb_0x1b(self): self.e = self._rr(self.e); return 8
    def cb_0x1c(self): self.h = self._rr(self.h); return 8
    def cb_0x1d(self): self.l = self._rr(self.l); return 8
    def cb_0x1e(self): self.mmu.write_byte(self._get_hl(), self._rr(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x1f(self): self.a = self._rr(self.a); return 8

    def cb_0x20(self): self.b = self._sla(self.b); return 8
    def cb_0x21(self): self.c = self._sla(self.c); return 8
    def cb_0x22(self): self.d = self._sla(self.d); return 8
    def cb_0x23(self): self.e = self._sla(self.e); return 8
    def cb_0x24(self): self.h = self._sla(self.h); return 8
    def cb_0x25(self): self.l = self._sla(self.l); return 8
    def cb_0x26(self): self.mmu.write_byte(self._get_hl(), self._sla(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x27(self): self.a = self._sla(self.a); return 8

    def cb_0x28(self): self.b = self._sra(self.b); return 8
    def cb_0x29(self): self.c = self._sra(self.c); return 8
    def cb_0x2a(self): self.d = self._sra(self.d); return 8
    def cb_0x2b(self): self.e = self._sra(self.e); return 8
    def cb_0x2c(self): self.h = self._sra(self.h); return 8
    def cb_0x2d(self): self.l = self._sra(self.l); return 8
    def cb_0x2e(self): self.mmu.write_byte(self._get_hl(), self._sra(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x2f(self): self.a = self._sra(self.a); return 8

    def cb_0x30(self): self.b = self._swap(self.b); return 8
    def cb_0x31(self): self.c = self._swap(self.c); return 8
    def cb_0x32(self): self.d = self._swap(self.d); return 8
    def cb_0x33(self): self.e = self._swap(self.e); return 8
    def cb_0x34(self): self.h = self._swap(self.h); return 8
    def cb_0x35(self): self.l = self._swap(self.l); return 8
    def cb_0x36(self): self.mmu.write_byte(self._get_hl(), self._swap(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x37(self): self.a = self._swap(self.a); return 8

    def cb_0x38(self): self.b = self._srl(self.b); return 8
    def cb_0x39(self): self.c = self._srl(self.c); return 8
    def cb_0x3a(self): self.d = self._srl(self.d); return 8
    def cb_0x3b(self): self.e = self._srl(self.e); return 8
    def cb_0x3c(self): self.h = self._srl(self.h); return 8
    def cb_0x3d(self): self.l = self._srl(self.l); return 8
    def cb_0x3e(self): self.mmu.write_byte(self._get_hl(), self._srl(self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x3f(self): self.a = self._srl(self.a); return 8

    def cb_0x40(self): self._bit(0, self.b); return 8
    def cb_0x41(self): self._bit(0, self.c); return 8
    def cb_0x42(self): self._bit(0, self.d); return 8
    def cb_0x43(self): self._bit(0, self.e); return 8
    def cb_0x44(self): self._bit(0, self.h); return 8
    def cb_0x45(self): self._bit(0, self.l); return 8
    def cb_0x46(self): self._bit(0, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x47(self): self._bit(0, self.a); return 8

    def cb_0x48(self): self._bit(1, self.b); return 8
    def cb_0x49(self): self._bit(1, self.c); return 8
    def cb_0x4a(self): self._bit(1, self.d); return 8
    def cb_0x4b(self): self._bit(1, self.e); return 8
    def cb_0x4c(self): self._bit(1, self.h); return 8
    def cb_0x4d(self): self._bit(1, self.l); return 8
    def cb_0x4e(self): self._bit(1, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x4f(self): self._bit(1, self.a); return 8

    def cb_0x50(self): self._bit(2, self.b); return 8
    def cb_0x51(self): self._bit(2, self.c); return 8
    def cb_0x52(self): self._bit(2, self.d); return 8
    def cb_0x53(self): self._bit(2, self.e); return 8
    def cb_0x54(self): self._bit(2, self.h); return 8
    def cb_0x55(self): self._bit(2, self.l); return 8
    def cb_0x56(self): self._bit(2, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x57(self): self._bit(2, self.a); return 8

    def cb_0x58(self): self._bit(3, self.b); return 8
    def cb_0x59(self): self._bit(3, self.c); return 8
    def cb_0x5a(self): self._bit(3, self.d); return 8
    def cb_0x5b(self): self._bit(3, self.e); return 8
    def cb_0x5c(self): self._bit(3, self.h); return 8
    def cb_0x5d(self): self._bit(3, self.l); return 8
    def cb_0x5e(self): self._bit(3, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x5f(self): self._bit(3, self.a); return 8

    def cb_0x60(self): self._bit(4, self.b); return 8
    def cb_0x61(self): self._bit(4, self.c); return 8
    def cb_0x62(self): self._bit(4, self.d); return 8
    def cb_0x63(self): self._bit(4, self.e); return 8
    def cb_0x64(self): self._bit(4, self.h); return 8
    def cb_0x65(self): self._bit(4, self.l); return 8
    def cb_0x66(self): self._bit(4, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x67(self): self._bit(4, self.a); return 8

    def cb_0x68(self): self._bit(5, self.b); return 8
    def cb_0x69(self): self._bit(5, self.c); return 8
    def cb_0x6a(self): self._bit(5, self.d); return 8
    def cb_0x6b(self): self._bit(5, self.e); return 8
    def cb_0x6c(self): self._bit(5, self.h); return 8
    def cb_0x6d(self): self._bit(5, self.l); return 8
    def cb_0x6e(self): self._bit(5, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x6f(self): self._bit(5, self.a); return 8

    def cb_0x70(self): self._bit(6, self.b); return 8
    def cb_0x71(self): self._bit(6, self.c); return 8
    def cb_0x72(self): self._bit(6, self.d); return 8
    def cb_0x73(self): self._bit(6, self.e); return 8
    def cb_0x74(self): self._bit(6, self.h); return 8
    def cb_0x75(self): self._bit(6, self.l); return 8
    def cb_0x76(self): self._bit(6, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x77(self): self._bit(6, self.a); return 8

    def cb_0x78(self): self._bit(7, self.b); return 8
    def cb_0x79(self): self._bit(7, self.c); return 8
    def cb_0x7a(self): self._bit(7, self.d); return 8
    def cb_0x7b(self): self._bit(7, self.e); return 8
    def cb_0x7c(self): self._bit(7, self.h); return 8
    def cb_0x7d(self): self._bit(7, self.l); return 8
    def cb_0x7e(self): self._bit(7, self.mmu.read_byte(self._get_hl())); return 12
    def cb_0x7f(self): self._bit(7, self.a); return 8

    def cb_0x80(self): self.b = self._res(0, self.b); return 8
    def cb_0x81(self): self.c = self._res(0, self.c); return 8
    def cb_0x82(self): self.d = self._res(0, self.d); return 8
    def cb_0x83(self): self.e = self._res(0, self.e); return 8
    def cb_0x84(self): self.h = self._res(0, self.h); return 8
    def cb_0x85(self): self.l = self._res(0, self.l); return 8
    def cb_0x86(self): self.mmu.write_byte(self._get_hl(), self._res(0, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x87(self): self.a = self._res(0, self.a); return 8

    def cb_0x88(self): self.b = self._res(1, self.b); return 8
    def cb_0x89(self): self.c = self._res(1, self.c); return 8
    def cb_0x8a(self): self.d = self._res(1, self.d); return 8
    def cb_0x8b(self): self.e = self._res(1, self.e); return 8
    def cb_0x8c(self): self.h = self._res(1, self.h); return 8
    def cb_0x8d(self): self.l = self._res(1, self.l); return 8
    def cb_0x8e(self): self.mmu.write_byte(self._get_hl(), self._res(1, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x8f(self): self.a = self._res(1, self.a); return 8

    def cb_0x90(self): self.b = self._res(2, self.b); return 8
    def cb_0x91(self): self.c = self._res(2, self.c); return 8
    def cb_0x92(self): self.d = self._res(2, self.d); return 8
    def cb_0x93(self): self.e = self._res(2, self.e); return 8
    def cb_0x94(self): self.h = self._res(2, self.h); return 8
    def cb_0x95(self): self.l = self._res(2, self.l); return 8
    def cb_0x96(self): self.mmu.write_byte(self._get_hl(), self._res(2, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x97(self): self.a = self._res(2, self.a); return 8

    def cb_0x98(self): self.b = self._res(3, self.b); return 8
    def cb_0x99(self): self.c = self._res(3, self.c); return 8
    def cb_0x9a(self): self.d = self._res(3, self.d); return 8
    def cb_0x9b(self): self.e = self._res(3, self.e); return 8
    def cb_0x9c(self): self.h = self._res(3, self.h); return 8
    def cb_0x9d(self): self.l = self._res(3, self.l); return 8
    def cb_0x9e(self): self.mmu.write_byte(self._get_hl(), self._res(3, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0x9f(self): self.a = self._res(3, self.a); return 8

    def cb_0xa0(self): self.b = self._res(4, self.b); return 8
    def cb_0xa1(self): self.c = self._res(4, self.c); return 8
    def cb_0xa2(self): self.d = self._res(4, self.d); return 8
    def cb_0xa3(self): self.e = self._res(4, self.e); return 8
    def cb_0xa4(self): self.h = self._res(4, self.h); return 8
    def cb_0xa5(self): self.l = self._res(4, self.l); return 8
    def cb_0xa6(self): self.mmu.write_byte(self._get_hl(), self._res(4, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xa7(self): self.a = self._res(4, self.a); return 8

    def cb_0xa8(self): self.b = self._res(5, self.b); return 8
    def cb_0xa9(self): self.c = self._res(5, self.c); return 8
    def cb_0xaa(self): self.d = self._res(5, self.d); return 8
    def cb_0xab(self): self.e = self._res(5, self.e); return 8
    def cb_0xac(self): self.h = self._res(5, self.h); return 8
    def cb_0xad(self): self.l = self._res(5, self.l); return 8
    def cb_0xae(self): self.mmu.write_byte(self._get_hl(), self._res(5, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xaf(self): self.a = self._res(5, self.a); return 8

    def cb_0xb0(self): self.b = self._res(6, self.b); return 8
    def cb_0xb1(self): self.c = self._res(6, self.c); return 8
    def cb_0xb2(self): self.d = self._res(6, self.d); return 8
    def cb_0xb3(self): self.e = self._res(6, self.e); return 8
    def cb_0xb4(self): self.h = self._res(6, self.h); return 8
    def cb_0xb5(self): self.l = self._res(6, self.l); return 8
    def cb_0xb6(self): self.mmu.write_byte(self._get_hl(), self._res(6, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xb7(self): self.a = self._res(6, self.a); return 8

    def cb_0xb8(self): self.b = self._res(7, self.b); return 8
    def cb_0xb9(self): self.c = self._res(7, self.c); return 8
    def cb_0xba(self): self.d = self._res(7, self.d); return 8
    def cb_0xbb(self): self.e = self._res(7, self.e); return 8
    def cb_0xbc(self): self.h = self._res(7, self.h); return 8
    def cb_0xbd(self): self.l = self._res(7, self.l); return 8
    def cb_0xbe(self): self.mmu.write_byte(self._get_hl(), self._res(7, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xbf(self): self.a = self._res(7, self.a); return 8
    def cb_0xc0(self): self.b = self._set(0, self.b); return 8
    def cb_0xc1(self): self.c = self._set(0, self.c); return 8
    def cb_0xc2(self): self.d = self._set(0, self.d); return 8
    def cb_0xc3(self): self.e = self._set(0, self.e); return 8
    def cb_0xc4(self): self.h = self._set(0, self.h); return 8
    def cb_0xc5(self): self.l = self._set(0, self.l); return 8
    def cb_0xc6(self): self.mmu.write_byte(self._get_hl(), self._set(0, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xc7(self): self.a = self._set(0, self.a); return 8

    def cb_0xc8(self): self.b = self._set(1, self.b); return 8
    def cb_0xc9(self): self.c = self._set(1, self.c); return 8
    def cb_0xca(self): self.d = self._set(1, self.d); return 8
    def cb_0xcb(self): self.e = self._set(1, self.e); return 8
    def cb_0xcc(self): self.h = self._set(1, self.h); return 8
    def cb_0xcd(self): self.l = self._set(1, self.l); return 8
    def cb_0xce(self): self.mmu.write_byte(self._get_hl(), self._set(1, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xcf(self): self.a = self._set(1, self.a); return 8

    def cb_0xd0(self): self.b = self._set(2, self.b); return 8
    def cb_0xd1(self): self.c = self._set(2, self.c); return 8
    def cb_0xd2(self): self.d = self._set(2, self.d); return 8
    def cb_0xd3(self): self.e = self._set(2, self.e); return 8
    def cb_0xd4(self): self.h = self._set(2, self.h); return 8
    def cb_0xd5(self): self.l = self._set(2, self.l); return 8
    def cb_0xd6(self): self.mmu.write_byte(self._get_hl(), self._set(2, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xd7(self): self.a = self._set(2, self.a); return 8

    def cb_0xd8(self): self.b = self._set(3, self.b); return 8
    def cb_0xd9(self): self.c = self._set(3, self.c); return 8
    def cb_0xda(self): self.d = self._set(3, self.d); return 8
    def cb_0xdb(self): self.e = self._set(3, self.e); return 8
    def cb_0xdc(self): self.h = self._set(3, self.h); return 8
    def cb_0xdd(self): self.l = self._set(3, self.l); return 8
    def cb_0xde(self): self.mmu.write_byte(self._get_hl(), self._set(3, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xdf(self): self.a = self._set(3, self.a); return 8

    def cb_0xe0(self): self.b = self._set(4, self.b); return 8
    def cb_0xe1(self): self.c = self._set(4, self.c); return 8
    def cb_0xe2(self): self.d = self._set(4, self.d); return 8
    def cb_0xe3(self): self.e = self._set(4, self.e); return 8
    def cb_0xe4(self): self.h = self._set(4, self.h); return 8
    def cb_0xe5(self): self.l = self._set(4, self.l); return 8
    def cb_0xe6(self): self.mmu.write_byte(self._get_hl(), self._set(4, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xe7(self): self.a = self._set(4, self.a); return 8

    def cb_0xe8(self): self.b = self._set(5, self.b); return 8
    def cb_0xe9(self): self.c = self._set(5, self.c); return 8
    def cb_0xea(self): self.d = self._set(5, self.d); return 8
    def cb_0xeb(self): self.e = self._set(5, self.e); return 8
    def cb_0xec(self): self.h = self._set(5, self.h); return 8
    def cb_0xed(self): self.l = self._set(5, self.l); return 8
    def cb_0xee(self): self.mmu.write_byte(self._get_hl(), self._set(5, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xef(self): self.a = self._set(5, self.a); return 8

    def cb_0xf0(self): self.b = self._set(6, self.b); return 8
    def cb_0xf1(self): self.c = self._set(6, self.c); return 8
    def cb_0xf2(self): self.d = self._set(6, self.d); return 8
    def cb_0xf3(self): self.e = self._set(6, self.e); return 8
    def cb_0xf4(self): self.h = self._set(6, self.h); return 8
    def cb_0xf5(self): self.l = self._set(6, self.l); return 8
    def cb_0xf6(self): self.mmu.write_byte(self._get_hl(), self._set(6, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xf7(self): self.a = self._set(6, self.a); return 8

    def cb_0xf8(self): self.b = self._set(7, self.b); return 8
    def cb_0xf9(self): self.c = self._set(7, self.c); return 8
    def cb_0xfa(self): self.d = self._set(7, self.d); return 8
    def cb_0xfb(self): self.e = self._set(7, self.e); return 8
    def cb_0xfc(self): self.h = self._set(7, self.h); return 8
    def cb_0xfd(self): self.l = self._set(7, self.l); return 8
    def cb_0xfe(self): self.mmu.write_byte(self._get_hl(), self._set(7, self.mmu.read_byte(self._get_hl()))); return 16
    def cb_0xff(self): self.a = self._set(7, self.a); return 8


    def _create_opcode_map(self):
        self.opcodes = {
            0x00: self.op_0x00, 0x01: self.op_0x01, 0x02: self.op_0x02, 0x03: self.op_0x03,
            0x04: self.op_0x04, 0x05: self.op_0x05, 0x06: self.op_0x06, 0x07: self.op_0x07,
            0x08: self.op_0x08, 0x09: self.op_0x09, 0x0A: self.op_0x0a, 0x0B: self.op_0x0b,
            0x0C: self.op_0x0c, 0x0D: self.op_0x0d, 0x0E: self.op_0x0e, 0x0F: self.op_0x0f,

            0x10: self.op_0x10, 0x11: self.op_0x11, 0x12: self.op_0x12, 0x13: self.op_0x13,
            0x14: self.op_0x14, 0x15: self.op_0x15, 0x16: self.op_0x16, 0x17: self.op_0x17,
            0x18: self.op_0x18, 0x19: self.op_0x19, 0x1A: self.op_0x1a, 0x1B: self.op_0x1b,
            0x1C: self.op_0x1c, 0x1D: self.op_0x1d, 0x1E: self.op_0x1e, 0x1F: self.op_0x1f,

            0x20: self.op_0x20, 0x21: self.op_0x21, 0x22: self.op_0x22, 0x23: self.op_0x23,
            0x24: self.op_0x24, 0x25: self.op_0x25, 0x26: self.op_0x26, 0x27: self.op_0x27,
            0x28: self.op_0x28, 0x29: self.op_0x29, 0x2A: self.op_0x2a, 0x2B: self.op_0x2b,
            0x2C: self.op_0x2c, 0x2D: self.op_0x2d, 0x2E: self.op_0x2e, 0x2F: self.op_0x2f,

            0x30: self.op_0x30, 0x31: self.op_0x31, 0x32: self.op_0x32, 0x33: self.op_0x33,
            0x34: self.op_0x34, 0x35: self.op_0x35, 0x36: self.op_0x36, 0x37: self.op_0x37,
            0x38: self.op_0x38, 0x39: self.op_0x39, 0x3A: self.op_0x3a, 0x3B: self.op_0x3b,
            0x3C: self.op_0x3c, 0x3D: self.op_0x3d, 0x3E: self.op_0x3e, 0x3F: self.op_0x3f,

            0x40: self.op_0x40, 0x41: self.op_0x41, 0x42: self.op_0x42, 0x43: self.op_0x43,
            0x44: self.op_0x44, 0x45: self.op_0x45, 0x46: self.op_0x46, 0x47: self.op_0x47, 
            0x48: self.op_0x48, 0x49: self.op_0x49, 0x4A: self.op_0x4a, 0x4B: self.op_0x4b, 
            0x4C: self.op_0x4c, 0x4D: self.op_0x4d, 0x4E: self.op_0x4e, 0x4F: self.op_0x4f, 

            0x50: self.op_0x50, 0x51: self.op_0x51, 0x52: self.op_0x52, 0x53: self.op_0x53,
            0x54: self.op_0x54, 0x55: self.op_0x55, 0x56: self.op_0x56, 0x57: self.op_0x57,
            0x58: self.op_0x58, 0x59: self.op_0x59, 0x5A: self.op_0x5a, 0x5B: self.op_0x5b,
            0x5C: self.op_0x5c, 0x5D: self.op_0x5d, 0x5E: self.op_0x5e, 0x5F: self.op_0x5f,

            0x60: self.op_0x60, 0x61: self.op_0x61, 0x62: self.op_0x62, 0x63: self.op_0x63,
            0x64: self.op_0x64, 0x65: self.op_0x65, 0x66: self.op_0x66, 0x67: self.op_0x67,
            0x68: self.op_0x68, 0x69: self.op_0x69, 0x6A: self.op_0x6a, 0x6B: self.op_0x6b,
            0x6C: self.op_0x6c, 0x6D: self.op_0x6d, 0x6E: self.op_0x6e, 0x6F: self.op_0x6f,

            0x70: self.op_0x70, 0x71: self.op_0x71, 0x72: self.op_0x72, 0x73: self.op_0x73,
            0x74: self.op_0x74, 0x75: self.op_0x75, 0x76: self.op_0x76, 0x77: self.op_0x77,
            0x78: self.op_0x78, 0x79: self.op_0x79, 0x7A: self.op_0x7a, 0x7B: self.op_0x7b,
            0x7C: self.op_0x7c, 0x7D: self.op_0x7d, 0x7E: self.op_0x7e, 0x7F: self.op_0x7f,

            0x80: self.op_0x80, 0x81: self.op_0x81, 0x82: self.op_0x82, 0x83: self.op_0x83,
            0x84: self.op_0x84, 0x85: self.op_0x85, 0x86: self.op_0x86, 0x87: self.op_0x87,
            0x88: self.op_0x88, 0x89: self.op_0x89, 0x8A: self.op_0x8a, 0x8B: self.op_0x8b,
            0x8C: self.op_0x8c, 0x8D: self.op_0x8d, 0x8E: self.op_0x8e, 0x8F: self.op_0x8f,

            0x90: self.op_0x90, 0x91: self.op_0x91, 0x92: self.op_0x92, 0x93: self.op_0x93,
            0x94: self.op_0x94, 0x95: self.op_0x95, 0x96: self.op_0x96, 0x97: self.op_0x97,
            0x98: self.op_0x98, 0x99: self.op_0x99, 0x9A: self.op_0x9a, 0x9B: self.op_0x9b,
            0x9C: self.op_0x9c, 0x9D: self.op_0x9d, 0x9E: self.op_0x9e, 0x9F: self.op_0x9f,

            0xA0: self.op_0xa0, 0xA1: self.op_0xa1, 0xA2: self.op_0xa2, 0xA3: self.op_0xa3,
            0xA4: self.op_0xa4, 0xA5: self.op_0xa5, 0xA6: self.op_0xa6, 0xA7: self.op_0xa7,
            0xA8: self.op_0xa8, 0xA9: self.op_0xa9, 0xAA: self.op_0xaa, 0xAB: self.op_0xab,
            0xAC: self.op_0xac, 0xAD: self.op_0xad, 0xAE: self.op_0xae, 0xAF: self.op_0xaf,

            0xB0: self.op_0xb0, 0xB1: self.op_0xb1, 0xB2: self.op_0xb2, 0xB3: self.op_0xb3,
            0xB4: self.op_0xb4, 0xB5: self.op_0xb5, 0xB6: self.op_0xb6, 0xB7: self.op_0xb7,
            0xB8: self.op_0xb8, 0xB9: self.op_0xb9, 0xBA: self.op_0xba, 0xBB: self.op_0xbb,
            0xBC: self.op_0xbc, 0xBD: self.op_0xbd, 0xBE: self.op_0xbe, 0xBF: self.op_0xbf,

            0xC0: self.op_0xc0, 0xC1: self.op_0xc1, 0xC2: self.op_0xc2, 0xC3: self.op_0xc3,
            0xC4: self.op_0xc4, 0xC5: self.op_0xc5, 0xC6: self.op_0xc6, 0xC7: self.op_0xc7,
            0xC8: self.op_0xc8, 0xC9: self.op_0xc9, 0xCA: self.op_0xca, 0xCB: self.op_0xcb,
            0xCC: self.op_0xcc, 0xCD: self.op_0xcd, 0xCE: self.op_0xce, 0xCF: self.op_0xcf,

            0xD0: self.op_0xd0, 0xD1: self.op_0xd1, 0xD2: self.op_0xd2, 0xD3: self.op_0xd3,
            0xD4: self.op_0xd4, 0xD5: self.op_0xd5, 0xD6: self.op_0xd6, 0xD7: self.op_0xd7,
            0xD8: self.op_0xd8, 0xD9: self.op_0xd9, 0xDA: self.op_0xda, 0xDB: self.op_0xdb,
            0xDC: self.op_0xdc, 0xDD: self.op_0xdd, 0xDE: self.op_0xde, 0xDF: self.op_0xdf,

            0xE0: self.op_0xe0, 0xE1: self.op_0xe1, 0xE2: self.op_0xe2, 0xE3: self.op_0xe3,
            0xE4: self.op_0xe4, 0xE5: self.op_0xe5, 0xE6: self.op_0xe6, 0xE7: self.op_0xe7,
            0xE8: self.op_0xe8, 0xE9: self.op_0xe9, 0xEA: self.op_0xea, 0xEB: self.op_0xeb,
            0xEC: self.op_0xec, 0xED: self.op_0xed, 0xEE: self.op_0xee, 0xEF: self.op_0xef,

            0xF0: self.op_0xf0, 0xF1: self.op_0xf1, 0xF2: self.op_0xf2, 0xF3: self.op_0xf3,
            0xF4: self.op_0xf4, 0xF5: self.op_0xf5, 0xF6: self.op_0xf6, 0xF7: self.op_0xf7,
            0xF8: self.op_0xf8, 0xF9: self.op_0xf9, 0xFA: self.op_0xfa, 0xFB: self.op_0xfb,
            0xFC: self.op_0xfc, 0xFD: self.op_0xfd, 0xFE: self.op_0xfe, 0xFF: self.op_0xff,
        }

    def op_0x07(self):
        """ 0x07: RLC """
        self.a = self._rlc(self.a)
        return 4

    def op_0x0f(self):
        """ 0x0F: RRC """
        self.a = self._rrc(self.a)
        return 4

    def op_0x14(self):
        """ 0x14: INC D """
        self.d = self._inc(self.d)
        return 4

    def op_0x15(self):
        """ 0x15: DEC D """
        self.d = self._dec(self.d)
        return 4

    def op_0x2b(self):
        """ 0x2B: DEC E """
        self._set_hl(self._get_hl()-1)

    def op_0x38(self):
        """ 0x38: JR C """
        return self._jr(self._get_flag_c())

    def op_0x3b(self):
        """ 0x3B: DEC SP """
        self.sp = (self.sp - 1) & 0xFFFF
        return 8

    def op_0x3f(self):
        """ 0x3F: CCF """
        return self._ccf()

    def op_0x66(self):
        """ 0x66: LD H, (HL) """
        self.h = self.mmu.read_byte(self._get_hl())
        return 8


    def op_0x67(self):
        """ 0x67: LD H, A """
        self.h = self.a
        return 4
    
    def op_0x76(self):
        """ 0x76: HALT """
        print("HALT")
        return 4

    def op_0x8f(self):
        """ 0x8F: ADC A, A"""
        self.a = self._adc(self.a)
        return 4

    def op_0x97(self):
        """ 0x97: SUB A, A """
        self.a = self._sub(self.a)
        return 4

    def op_0x9f(self):
        """ 0x9F: SBC A, A """
        self.a = self._sbc(self.a)
        return 4

    def op_0xbf(self):
        """ CP A """
        self._cp(self.a)
        return 4

    def op_0xc7(self):
        """ 0xC7: RST 00H """
        self._push_word(self.pc)
        self.pc = 0x0000
        return 16

    def op_0xcf(self):
        """ 0xCF: RST 08H """
        self._push_word(self.pc)
        self.pc = 0x0008
        return 16

    def op_0xd3(self):
        """ 0xD3: Forbidden """
        print("Forbidden")
        return 4

    def op_0xd7(self):
        """ 0xD7: RST 10H """
        self._push_word(self.pc)
        self.pc = 0x0010
        return 16

    def op_0xdb(self):
        """ 0xDB: Forbidden """
        print("Forbidden")
        return 4

    def op_0xdd(self):
        """ 0xDD: Forbidden """
        print("Forbidden")
        return 4

    def op_0xdf(self):
        """ 0xDF: RST 18H """
        self._push_word(self.pc)
        self.pc = 0x0018
        return 16

    def op_0xe3(self):
        """ 0xE3: Forbidden """
        print("Forbidden")
        return 4

    def op_0xe4(self):
        """ 0xE4: Forbidden """
        print("Forbidden")
        return 4

    def op_0xe7(self):
        """ 0xE7: RST 20H """
        self._push_word(self.pc)
        self.pc = 0x0020
        return 16
    
    def op_0xeb(self):
        """ 0xE7: Forbidden """
        print("Forbidden")
        return 4

    def op_0xec(self):
        """ 0xEC: Forbidden """
        print("Forbidden")
        return 4

    def op_0xed(self):
        """ 0xED: Forbidden """
        print("Forbidden")
        return 4

    def op_0xf2(self):
        """ 0xF2: LD A, (C) """
        self.a = self.mmu.read_byte(0xFF00 + self.c)
        return 8

    def op_0xf4(self):
        """ 0xF4: Forbidden """
        print("Forbidden")
        return 4

    def op_0xf7(self):
        """ 0xF7: RST 30H """
        self._push_word(self.pc)
        self.pc = 0x0030
        return 16

    def op_0xfc(self):
        """ 0xFC: Forbidden """
        print("Forbidden")
        return 4

    def op_0xfd(self):
        """ 0xFD: Forbidden """
        print("Forbidden")
        return 4

    # --- Opcode Implementations ---
    def op_0x00(self):
        """ 0x00: NOP """
        return 4

    def op_0xfb(self): self.ime = 1; return 4

    def op_0x17(self):
        """0x17: RLA"""
        carry = self._get_flag_c()
        self._set_flag_c((self.a >> 7) & 1)
        self.a = ((self.a << 1) | carry) & 0xFF
        self._set_flag_z(0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        return 4

    def op_0x24(self):
        """ 0x24: INC H """
        self.h = self._inc(self.h)
        return 4
    
    def op_0x6e(self):
        self.l = self.mmu.read_byte(self._get_hl())
        return 8


    def op_0x27(self):
        """ 0x27: DAA """
        # This implementation is incomplete and may not be fully accurate.
        # Needs more research and testing.
        a = self.a
        n_flag = self._get_flag_n()
        h_flag = self._get_flag_h()
        c_flag = self._get_flag_c()

        if not n_flag:
            if c_flag or a > 0x99:
                a += 0x60
                self._set_flag_c(1)
            if h_flag or (a & 0x0F) > 0x09:
                a += 0x06
        else:
            if c_flag:
                a -= 0x60
            if h_flag:
                a -= 0x06

        a &= 0xFF
        self._set_flag_z(a == 0)
        self._set_flag_h(0)
        self.a = a
        return 4

    def op_0x29(self):
        """ 0x29: ADD HL, HL """
        hl = self._get_hl()
        result = hl + hl
        self._set_flag_n(0)
        self._set_flag_h((hl & 0xFFF) + (hl & 0xFFF) > 0xFFF)
        self._set_flag_c(result > 0xFFFF)
        self._set_hl(result & 0xFFFF)
        return 8

    def op_0x1f(self):
        self.a = self._rr(self.a)
        return 4

    def op_0x33(self):
        """ 0x33: INC SP """
        self.sp = (self.sp + 1) & 0xFFFF
        return 8

    def op_0x1b(self):
        """ 0x1B: DEC DE"""
        self._set_de(self._get_de()-1)
        return 8
    
    def op_0x35(self):
        """ 0x35: DEC HL """
        self._set_hl(self._get_hl()-1)
        return 8
    
    def op_0x34(self):
        """ 0x34: INC HL"""
        self._set_hl(self._get_hl()+1)
        return 8

    def op_0x37(self):
        """ 0x37: SCF """
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(1)
        return 4
    def op_0x1d(self): self.e = self._dec(self.e); return 4
    def op_0x40(self): self.b = self.b; return 4
    def op_0x41(self): self.b = self.c; return 4
    def op_0x42(self): self.b = self.d; return 4
    def op_0x43(self): self.b = self.e; return 4
    def op_0x44(self): self.b = self.h; return 4
    def op_0x45(self): self.b = self.l; return 4
    def op_0x48(self): self.c = self.b; return 4
    def op_0x49(self): self.c = self.c; return 4
    def op_0x4a(self): self.c = self.d; return 4
    def op_0x4b(self): self.c = self.e; return 4
    def op_0x4c(self): self.c = self.h; return 4
    def op_0x4d(self): self.c = self.l; return 4
    def op_0x50(self): self.d = self.b; return 4
    def op_0x51(self): self.d = self.c; return 4
    def op_0x52(self): self.d = self.d; return 4
    def op_0x53(self): self.d = self.e; return 4
    def op_0x54(self): self.d = self.h; return 4
    def op_0x55(self): self.d = self.l; return 4
    def op_0x58(self): self.e = self.b; return 4
    def op_0x59(self): self.e = self.c; return 4
    def op_0x5a(self): self.e = self.d; return 4
    def op_0x5b(self): self.e = self.e; return 4
    def op_0x5c(self): self.e = self.h; return 4
    def op_0x5d(self): self.e = self.l; return 4
    def op_0x60(self): self.h = self.b; return 4
    def op_0x61(self): self.h = self.c; return 4
    def op_0x62(self): self.h = self.d; return 4
    def op_0x63(self): self.h = self.e; return 4
    def op_0x64(self): self.h = self.h; return 4
    def op_0x65(self): self.h = self.l; return 4
    def op_0x68(self): self.l = self.b; return 4
    def op_0x69(self): self.l = self.c; return 4
    def op_0x6a(self): self.l = self.d; return 4
    def op_0x6b(self): self.l = self.e; return 4
    def op_0x6c(self): self.l = self.h; return 4
    def op_0x6d(self): self.l = self.l; return 4
    def op_0x70(self): self.mmu.write_byte(self._get_hl(), self.b); return 8
    def op_0x71(self): self.mmu.write_byte(self._get_hl(), self.c); return 8
    def op_0x72(self): self.mmu.write_byte(self._get_hl(), self.d); return 8
    def op_0x73(self): self.mmu.write_byte(self._get_hl(), self.e); return 8
    def op_0x74(self): self.mmu.write_byte(self._get_hl(), self.h); return 8
    def op_0x75(self): self.mmu.write_byte(self._get_hl(), self.l); return 8
    def op_0x80(self): self.a = self._add(self.b); return 4
    def op_0x81(self): self.a = self._add(self.c); return 4
    def op_0x82(self): self.a = self._add(self.d); return 4
    def op_0x83(self): self.a = self._add(self.e); return 4
    def op_0x84(self): self.a = self._add(self.h); return 4
    def op_0x85(self): self.a = self._add(self.l); return 4
    def op_0x86(self): self.a = self._add(self.mmu.read_byte(self._get_hl())); return 8
    def op_0x88(self): self.a = self._adc(self.b); return 4
    def op_0x89(self): self.a = self._adc(self.c); return 4
    def op_0x8a(self): self.a = self._adc(self.d); return 4
    def op_0x8b(self): self.a = self._adc(self.e); return 4
    def op_0x8c(self): self.a = self._adc(self.h); return 4
    def op_0x8d(self): self.a = self._adc(self.l); return 4
    def op_0x8e(self): self.a = self._adc(self.mmu.read_byte(self._get_hl())); return 8
    def op_0x90(self): self.a = self._sub(self.b); return 4
    def op_0x91(self): self.a = self._sub(self.c); return 4
    def op_0x92(self): self.a = self._sub(self.d); return 4
    def op_0x93(self): self.a = self._sub(self.e); return 4
    def op_0x94(self): self.a = self._sub(self.h); return 4
    def op_0x95(self): self.a = self._sub(self.l); return 4
    def op_0x96(self): self.a = self._sub(self.mmu.read_byte(self._get_hl())); return 8
    def op_0x98(self): self.a = self._sbc(self.b); return 4
    def op_0x99(self): self.a = self._sbc(self.c); return 4
    def op_0x9a(self): self.a = self._sbc(self.d); return 4
    def op_0x9b(self): self.a = self._sbc(self.e); return 4
    def op_0x9c(self): self.a = self._sbc(self.h); return 4
    def op_0x9d(self): self.a = self._sbc(self.l); return 4
    def op_0x9e(self): self.a = self._sbc(self.mmu.read_byte(self._get_hl())); return 8
    def op_0xa0(self): self.a &= self.b; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa1(self): self.a &= self.c; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa2(self): self.a &= self.d; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa3(self): self.a &= self.e; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa4(self): self.a &= self.h; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa5(self): self.a &= self.l; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 4
    def op_0xa6(self): val = self.mmu.read_byte(self._get_hl()); self.a &= val; self._set_flags_alu(self.a); self._set_flag_h(1); self._set_flag_c(0); return 8
    def op_0xa8(self): self.a ^= self.b; self._set_flags_alu(self.a); return 4
    def op_0xa9(self): self.a ^= self.c; self._set_flags_alu(self.a); return 4
    def op_0xaa(self): self.a ^= self.d; self._set_flags_alu(self.a); return 4
    def op_0xab(self): self.a ^= self.e; self._set_flags_alu(self.a); return 4
    def op_0xac(self): self.a ^= self.h; self._set_flags_alu(self.a); return 4
    def op_0xad(self): self.a ^= self.l; self._set_flags_alu(self.a); return 4
    def op_0xae(self): val = self.mmu.read_byte(self._get_hl()); self.a ^= val; self._set_flags_alu(self.a); return 8
    def op_0xb0(self): self.a |= self.b; self._set_flags_alu(self.a); return 4
    def op_0xb1(self): self.a |= self.c; self._set_flags_alu(self.a); return 4
    def op_0xb2(self): self.a |= self.d; self._set_flags_alu(self.a); return 4
    def op_0xb3(self): self.a |= self.e; self._set_flags_alu(self.a); return 4
    def op_0xb4(self): self.a |= self.h; self._set_flags_alu(self.a); return 4
    def op_0xb5(self): self.a |= self.l; self._set_flags_alu(self.a); return 4
    def op_0xb6(self): val = self.mmu.read_byte(self._get_hl()); self.a |= val; self._set_flags_alu(self.a); return 8
    def op_0xb8(self): self._cp(self.b); return 4
    def op_0xb9(self): self._cp(self.c); return 4
    def op_0xba(self): self._cp(self.d); return 4
    def op_0xbb(self): self._cp(self.e); return 4
    def op_0xbc(self): self._cp(self.h); return 4
    def op_0xbd(self): self._cp(self.l); return 4
    def op_0xbe(self): self._cp(self.mmu.read_byte(self._get_hl())); return 8

    def op_0xc4(self):
        """ 0xC4: CALL NZ, nn """
        addr = self._read_next_word()
        if not self._get_flag_z():
            self._push_word(self.pc)
            self.pc = addr
            return 24
        else:
            return 12

    def op_0xc6(self):
        """ 0xC6: ADD A, d8 """
        val = self._read_next_byte()
        result = self.a + val
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (val & 0x0F) > 0x0F)
        self._set_flag_c(result > 0xFF)
        self.a = result & 0xFF
        return 8

    def op_0xcc(self):
        """ 0xCC: CALL Z, nn """
        addr = self._read_next_word()
        if self._get_flag_z():
            self._push_word(self.pc)
            self.pc = addr
            return 24
        else:
            return 12

    def op_0xd0(self):
        """ 0xD0: RET NC """
        if not self._get_flag_c():
            self.pc = self._pop_word()
            return 20
        else:
            return 8

    def op_0xd2(self):
        """ 0xD2: JP NC, nn """
        addr = self._read_next_word()
        if not self._get_flag_c():
            self.pc = addr
            return 16
        else:
            return 12

    def op_0xd4(self):
        """ 0xD4: CALL NC, nn """
        addr = self._read_next_word()
        if not self._get_flag_c():
            self._push_word(self.pc)
            self.pc = addr
            return 24
        else:
            return 12

    def op_0xd6(self):
        """ 0xD6: SUB d8 """
        val = self._read_next_byte()
        result = self.a - val
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(1)
        self._set_flag_h((self.a & 0x0F) < (val & 0x0F))
        self._set_flag_c(self.a < val)
        self.a = result & 0xFF
        return 8

    def op_0xd8(self):
        """ 0xD8: RET C """
        if self._get_flag_c():
            self.pc = self._pop_word()
            return 20
        else:
            return 8

    def op_0xd9(self):
        """ 0xD9: RETI """
        self.ime = 1
        self.pc = self._pop_word()
        return 16

    def op_0xda(self):
        """ 0xDA: JP C, nn """
        addr = self._read_next_word()
        if self._get_flag_c():
            self.pc = addr
            return 16
        else:
            return 12

    def op_0xdc(self):
        """ 0xDC: CALL C, nn """
        addr = self._read_next_word()
        if self._get_flag_c():
            self._push_word(self.pc)
            self.pc = addr
            return 24
        else:
            return 12

    def op_0xde(self):
        """ 0xDE: SBC A, d8 """
        val = self._read_next_byte()
        carry = self._get_flag_c()
        result = self.a - val - carry
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(1)
        self._set_flag_h(((self.a & 0x0F) - (val & 0x0F) - carry) < 0)
        self._set_flag_c(result < 0)
        self.a = result & 0xFF
        return 8

    def op_0xe8(self):
        """ 0xE8: ADD SP, r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        result = self.sp + offset
        self._set_flag_z(0)
        self._set_flag_n(0)
        self._set_flag_h((self.sp & 0x0F) + (offset & 0x0F) > 0x0F)
        self._set_flag_c((self.sp & 0xFF) + (offset & 0xFF) > 0xFF)
        self.sp = result & 0xFFFF
        return 16

    def op_0xee(self):
        """ 0xEE: XOR d8 """
        val = self._read_next_byte()
        self.a ^= val
        self._set_flags_alu(self.a)
        return 8

    def op_0xf6(self):
        """ 0xF6: OR d8 """
        val = self._read_next_byte()
        self.a |= val
        self._set_flags_alu(self.a)
        return 8

    def op_0xf8(self):
        """ 0xF8: LD HL, SP+r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        result = self.sp + offset
        self._set_flag_z(0)
        self._set_flag_n(0)
        self._set_flag_h((self.sp & 0x0F) + (offset & 0x0F) > 0x0F)
        self._set_flag_c((self.sp & 0xFF) + (offset & 0xFF) > 0xFF)
        self._set_hl(result & 0xFFFF)
        return 12

    def op_0xf9(self):
        """ 0xF9: LD SP, HL """
        self.sp = self._get_hl()
        return 8

    def op_0x04(self):
        """ 0x04: INC B """
        self.b = self._inc(self.b)
        return 4

    def op_0x10(self):
        """0x10: STOP"""
        return 4

    def op_0x17(self):
        """0x17: RLA"""
        carry = self._get_flag_c()
        self._set_flag_c((self.a >> 7) & 1)
        self.a = ((self.a << 1) | carry) & 0xFF
        self._set_flag_z(0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        return 4

    def op_0x24(self):
        """ 0x24: INC H """
        self.h = self._inc(self.h)
        return 4

    def op_0x27(self):
        """ 0x27: DAA """
        #need to double check this
        a = self.a
        n_flag = self._get_flag_n()
        h_flag = self._get_flag_h()
        c_flag = self._get_flag_c()

        if not n_flag:
            if c_flag or a > 0x99:
                a += 0x60
                self._set_flag_c(1)
            if h_flag or (a & 0x0F) > 0x09:
                a += 0x06
        else:
            if c_flag:
                a -= 0x60
            if h_flag:
                a -= 0x06

        a &= 0xFF
        self._set_flag_z(a == 0)
        self._set_flag_h(0)
        self.a = a
        return 4

    def op_0x29(self):
        """ 0x29: ADD HL, HL """
        hl = self._get_hl()
        result = hl + hl
        self._set_flag_n(0)
        self._set_flag_h((hl & 0xFFF) + (hl & 0xFFF) > 0xFFF)
        self._set_flag_c(result > 0xFFFF)
        self._set_hl(result & 0xFFFF)
        return 8

    def op_0x33(self):
        """ 0x33: INC SP """
        self.sp = (self.sp + 1) & 0xFFFF
        return 8


    def op_0x06(self): self.b = self._read_next_byte(); return 8
    def op_0x0e(self): self.c = self._read_next_byte(); return 8
    def op_0x16(self): self.d = self._read_next_byte(); return 8
    def op_0x1e(self): self.e = self._read_next_byte(); return 8
    def op_0x1c(self): self.e = self._inc(self.e); return 4
    def op_0x26(self): self.h = self._read_next_byte(); return 8
    def op_0x2e(self): self.l = self._read_next_byte(); return 8
    def op_0x7f(self): return 4 # LD A, A
    def op_0x78(self): self.a = self.b; return 4
    def op_0x79(self): self.a = self.c; return 4
    def op_0x7a(self): self.a = self.d; return 4
    def op_0x7b(self): self.a = self.e; return 4
    def op_0x7c(self): self.a = self.h; return 4
    def op_0x7d(self): self.a = self.l; return 4
    def op_0x02(self): self.mmu.write_byte(self._get_bc(), self.a); return 8
    def op_0x12(self): self.mmu.write_byte(self._get_de(), self.a); return 8
    def op_0x22(self): self.mmu.write_byte(self._get_hl(), self.a); self._set_hl(self._get_hl() + 1); return 8
    def op_0x32(self): self.mmu.write_byte(self._get_hl(), self.a); self._set_hl(self._get_hl() - 1); return 8
    def op_0x0a(self): self.a = self.mmu.read_byte(self._get_bc()); return 8
    def op_0x1a(self): self.a = self.mmu.read_byte(self._get_de()); return 8
    def op_0x2a(self): self.a = self.mmu.read_byte(self._get_hl()); self._set_hl(self._get_hl() + 1); return 8
    def op_0x3a(self): self.a = self.mmu.read_byte(self._get_hl()); self._set_hl(self._get_hl() - 1); return 8
    def op_0x3e(self): self.a = self._read_next_byte(); return 8
    def op_0x36(self): self.mmu.write_byte(self._get_hl(), self._read_next_byte()); return 12
    def op_0x77(self): self.mmu.write_byte(self._get_hl(), self.a); return 8
    def op_0x57(self): self.d = self.a; return 4
    def op_0x7e(self): self.a = self.mmu.read_byte(self._get_hl()); return 8
    def op_0xe0(self): self.mmu.write_byte(0xFF00 + self._read_next_byte(), self.a); return 12
    def op_0xe2(self): self.mmu.write_byte(0xFF00 + self.c, self.a); return 8
    def op_0xea(self): self.mmu.write_byte(self._read_next_word(), self.a); return 16
    def op_0xf0(self): self.a = self.mmu.read_byte(0xFF00 + self._read_next_byte()); return 12
    def op_0x56(self): self.d = self.mmu.read_byte(self._get_hl()); return 8
    def op_0x5f(self): self.e = self.a; return 4
    def op_0x5e(self): self.e = self.mmu.read_byte(self._get_hl()); return 8
    def op_0xfa(self): self.a = self.mmu.read_byte(self._read_next_word()); return 16
    def op_0x4e(self): self.c = self.mmu.read_byte(self._get_hl()); return 8
    def op_0x46(self): self.b = self.mmu.read_byte(self._get_hl()); return 8
    def op_0x69(self): self.l = self.c; return 4
    def op_0x60(self): self.h = self.b; return 4
    def op_0x6f(self): self.l = self.a; return 4
    def op_0xf3(self): self.a = self.mmu.read_byte(self.c); return 4

    def op_0x01(self): self._set_bc(self._read_next_word()); return 12
    def op_0x11(self): self._set_de(self._read_next_word()); return 12
    def op_0x21(self): self._set_hl(self._read_next_word()); return 12
    def op_0x31(self): self.sp = self._read_next_word(); return 12
    def op_0xe1(self): self._set_hl(self._pop_word()); return 12
    def op_0xf5(self): self._push_word((self.a << 8) | self.f); return 16
    def op_0xc5(self): self._push_word(self._get_bc()); return 16
    def op_0xd5(self): self._push_word(self._get_de()); return 16
    def op_0xe5(self): self._push_word(self._get_hl()); return 16
    def op_0xd1(self): self._set_de(self._pop_word()); return 12
    def op_0xc1(self): self._set_bc(self._pop_word()); return 12
    def op_0xf1(self):
        val = self._pop_word()
        self.a = (val >> 8) & 0xFF
        self.f = val & 0xFF & 0xF0 # Only upper 4 bits of F are used
        return 12

    def op_0x19(self):
        """ 0x19: ADD HL, DE """
        hl = self._get_hl()
        de = self._get_de()
        result = hl + de
        self._set_flag_n(0)
        self._set_flag_h((hl & 0xFFF) + (de & 0xFFF) > 0xFFF)
        self._set_flag_c(result > 0xFFFF)
        self._set_hl(result)
        return 8

    def op_0x23(self): self._set_hl(self._get_hl() + 1); return 8 # INC HL
    def op_0x13(self): self._set_de(self._get_de() + 1); return 8 # INC DE
    def op_0x03(self): self._set_bc(self._get_bc() + 1); return 8 # INC BC
    def op_0x39(self):
        """ 0x39: ADD HL, SP """
        hl = self._get_hl()
        sp = self.sp
        result = hl + sp
        self._set_flag_n(0)
        self._set_flag_h((hl & 0xFFF) + (sp & 0xFFF) > 0xFFF)
        self._set_flag_c(result > 0xFFFF)
        self._set_hl(result)
        return 8

    def op_0x09(self):
        """ 0x09: ADD HL, BC """
        hl = self._get_hl()
        bc = self._get_bc()
        result = hl + bc
        self._set_flag_n(0)
        self._set_flag_h((hl & 0xFFF) + (bc & 0xFFF) > 0xFFF)
        self._set_flag_c(result > 0xFFFF)
        self._set_hl(result)
        return 8

    # --- 8-bit ALU ---
    def op_0xaf(self):
        """ 0xAF: XOR A """
        self.a ^= self.a
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4

    def op_0x05(self):
        """ 0x05: DEC B """
        self.b = self._dec(self.b)
        return 4

    def op_0x0d(self):
        """ 0x0D: DEC C """
        self.c = self._dec(self.c)
        return 4

    def op_0x0c(self):
        """ 0x0C: INC C """
        self.c = self._inc(self.c)
        return 4

    def op_0x0b(self):
        """ 0x0B: DEC BC """
        self._set_bc(self._get_bc() - 1)
        return 8

    def op_0x2c(self):
        """ 0x2C: INC L """
        self.l = self._inc(self.l)
        return 4

    def op_0x3c(self):
        """ 0x3C: INC A """
        self.a = self._inc(self.a)
        return 4

    def op_0x25(self):
        """ 0x25: DEC H """
        self.h = self._dec(self.h)
        return 4

    def op_0x2d(self):
        """ 0x2D: DEC L """
        self.l = self._dec(self.l)
        return 4

    def op_0x3d(self):
        """ 0x3D: DEC A """
        self.a = self._dec(self.a)
        return 4

    def op_0xa7(self):
        """ 0xA7: AND A """
        self.a &= self.a
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(1)
        self._set_flag_c(0)
        return 4

    def op_0xb1(self):
        """ 0xB1: OR C """
        self.a |= self.c
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4

    def op_0x2f(self):
        """ 0x2F: CPL """
        self.a = ~self.a & 0xFF
        self._set_flag_n(1)
        self._set_flag_h(1)
        return 4

    def op_0x87(self):
        """ 0x87: ADD A, A """
        result = self.a + self.a
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (self.a & 0x0F) > 0x0F)
        self._set_flag_c(result > 0xFF)
        self.a = result & 0xFF
        return 4

    def op_0xb9(self):
        """ 0xB9: CP C """
        val = self.c
        result = self.a - val
        self._set_flag_z(result == 0)
        self._set_flag_n(1)
        self._set_flag_h((self.a & 0x0F) < (val & 0x0F))
        self._set_flag_c(self.a < val)
        return 4

    def op_0xb2(self):
        """ 0xB2: OR D """
        self.a |= self.d
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4

    def op_0xe6(self):
        """ 0xE6: AND n """
        self.a &= self._read_next_byte()
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(1)
        self._set_flag_c(0)
        return 8

    def op_0x47(self):
        """ 0x47: LD B, A """
        self.b = self.a
        return 4

    def op_0xb0(self):
        """ 0xB0: OR B """
        self.a |= self.b
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4
    
    def op_0xb7(self):
        """ 0xB0: OR A """
        self.a |= self.a
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4

    def op_0x4f(self):
        """ 0x4F: LD C, A """
        self.c = self.a
        return 4

    def op_0xa9(self):
        """ 0xA9: XOR C """
        self.a ^= self.c
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(0)
        self._set_flag_c(0)
        return 4

    def op_0xa1(self):
        """ 0xA1: AND C """
        self.a &= self.c
        self._set_flag_z(self.a == 0)
        self._set_flag_n(0)
        self._set_flag_h(1)
        self._set_flag_c(0)
        return 4

    def op_0xce(self):
        """ 0xCE: ADC A, n """
        val = self._read_next_byte()
        carry = self._get_flag_c()
        result = self.a + val + carry
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (val & 0x0F) + carry > 0x0F)
        self._set_flag_c(result > 0xFF)
        self.a = result & 0xFF
        return 8

    def op_0x85(self):
        """ 0x85: ADD A, L """
        val = self.l
        result = self.a + val
        self._set_flag_z((result & 0xFF) == 0)
        self._set_flag_n(0)
        self._set_flag_h((self.a & 0x0F) + (val & 0x0F) > 0x0F)
        self._set_flag_c(result > 0xFF)
        self.a = result & 0xFF
        return 4

    def op_0xfe(self):
        """ 0xFE: CP n """
        val = self._read_next_byte()
        result = self.a - val
        self._set_flag_z(result == 0)
        self._set_flag_n(1)
        self._set_flag_h((self.a & 0x0F) < (val & 0x0F))
        self._set_flag_c(self.a < val)
        return 8

    # --- Jumps ---
    def op_0xc3(self):
        """ 0xC3: JP nn """
        self.pc = self._read_next_word()
        return 16

    def op_0x20(self):
        """ 0x20: JR NZ, r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        
        if not self._get_flag_z():
            self.pc += offset
            return 12
        else:
            return 8

    def op_0x28(self):
        """ 0x28: JR Z, r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        
        if self._get_flag_z():
            self.pc += offset
            return 12
        else:
            return 8

    def op_0x18(self):
        """ 0x18: JR r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        self.pc += offset
        return 12

    def op_0xc0(self):
        """ 0xC0: RET NZ """
        if not self._get_flag_z():
            self.pc = self._pop_word()
            return 20
        else:
            return 8

    def op_0xc2(self):
        """ 0xC2: JP NZ, nn """
        addr = self._read_next_word()
        if not self._get_flag_z():
            self.pc = addr
            return 16
        else:
            return 12

    def op_0xca(self):
        """ 0xCA: JP Z, nn """
        addr = self._read_next_word()
        if self._get_flag_z():
            self.pc = addr
            return 16
        else:
            return 12

    def op_0x30(self):
        """ 0x30: JR NC, r8 """
        offset = self._read_next_byte()
        if offset > 127:
            offset -= 256
        
        if not self._get_flag_c():
            self.pc += offset
            return 12
        else:
            return 8

    def op_0xc8(self):
        """ 0xC8: RET Z """
        if self._get_flag_z():
            self.pc = self._pop_word()
            return 20
        else:
            return 8

    def op_0xc9(self):
        """ 0xC9: RET """
        self.pc = self._pop_word()
        return 16

    def op_0xcd(self):
        """ 0xCD: CALL nn """
        addr = self._read_next_word()
        self._push_word(self.pc)
        self.pc = addr
        return 24

    def op_0xef(self):
        """ 0xEF: RST 28H """
        self._push_word(self.pc)
        self.pc = 0x0028
        return 16

    def op_0xff(self):
        """ 0xFF: RST 38H """
        self._push_word(self.pc)
        self.pc = 0x0038
        return 16

    def op_0xe9(self):
        """ 0xE9: JP (HL) """
        self.pc = self._get_hl()
        return 4

    def op_0x08(self):
        """ 0x08: LD (nn), SP """
        addr = self._read_next_word()
        self.mmu.write_byte(addr, self.sp & 0xFF)
        self.mmu.write_byte(addr + 1, (self.sp >> 8) & 0xFF)
        return 20

    def op_0xcb(self):
        """ CB-prefixed opcodes """
        opcode = self._read_next_byte()
        return self._handle_cb_opcode(opcode)

    def _handle_cb_opcode(self, opcode):
        return self.cbcodes[opcode]()


    
