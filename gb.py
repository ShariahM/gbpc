import pygame
from cpu import CPU
from mmu import MMU
from ppu import PPU

class Gameboy:
    def __init__(self):
        pygame.init()
        self.screen_width = 160
        self.screen_height = 144
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Gameboy Emulator")
        self.clock = pygame.time.Clock()
        self.running = True

        self.mmu = MMU()
        self.cpu = CPU(self.mmu)
        self.ppu = PPU(self.mmu, self.cpu)

    def run(self):
        self.mmu.load_rom('roms/cpu_instrs.gb')
        #self.mmu.load_rom('roms/tetris.gb')

        
        # Gameboy clock speed is 4.194304 MHz. At 60 FPS, this is ~70,000 cycles per frame.
        cycles_per_frame = 4194304 // 60

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            cycles_this_frame = 0
            while cycles_this_frame < cycles_per_frame:
                cycles = self.cpu.step()
                self.ppu.step(cycles)
                cycles_this_frame += cycles

            self.draw_framebuffer()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def draw_framebuffer(self):
        for y, row in enumerate(self.ppu.framebuffer):
            for x, color in enumerate(row):
                self.screen.set_at((x, y), color)

if __name__ == "__main__":
    gb = Gameboy()
    gb.run()