import pygame
import numpy as np
import sys
from random import randint

class chip8core:
    def initialize(self):
        '''
        Initializes cpu core components.
        '''
        global pc, I, V, stack, sp, memory, gfx, delay_timer, sound_timer, surf, keys, window, drawflag

        pc = 0x200 #Program counter starts at 0x200
        I = 0 #Index register
        sp = 0 #Stack pointer

        #Stack, register, memory. "uint" specifies the unsigned integer datatype (8: max = 255, 16: max =  65535)
        stack = np.array([0 for i in range(16)], dtype=np.uint16)
        V = np.array([0 for i in range(16)], dtype=np.uint8)
        memory = np.array([0 for i in range(4096)], dtype=np.uint8)

        pygame.init()
        #Initializes screen
        window = pygame.display.set_mode((1024, 512), pygame.FULLSCREEN)
        surf = pygame.Surface((64, 32))
        gfx = pygame.PixelArray(surf)

        chip8_fontset = [
            0xF0, 0x90, 0x90, 0x90, 0xF0,
            0x20, 0x60, 0x20, 0x20, 0x70,
            0xF0, 0x10, 0xF0, 0x80, 0xF0,
            0xF0, 0x10, 0xF0, 0x10, 0xF0,
            0x90, 0x90, 0xF0, 0x10, 0x10,
            0xF0, 0x80, 0xF0, 0x10, 0xF0,
            0xF0, 0x80, 0xF0, 0x90, 0xF0,
            0xF0, 0x10, 0x20, 0x40, 0x40,
            0xF0, 0x90, 0xF0, 0x90, 0xF0,
            0xF0, 0x90, 0xF0, 0x10, 0xF0,
            0xF0, 0x90, 0xF0, 0x90, 0x90,
            0xE0, 0x90, 0xE0, 0x90, 0xE0,
            0xF0, 0x80, 0x80, 0x80, 0xF0,
            0xE0, 0x90, 0x90, 0x90, 0xE0,
            0xF0, 0x80, 0xF0, 0x80, 0xF0,
            0xF0, 0x80, 0xF0, 0x80, 0x80
            ]

        #Loads into memory
        for i in range(80):
            memory[i] = chip8_fontset[i]

        #Timers
        delay_timer = 0
        sound_timer = 0

        #Initializes keys
        keys = [0 for i in range(16)]

        #Drawflag
        drawflag = False


    def execute_opcode(opcode):
        '''
        Fetches opcode
        Decodes opcode
        Executes opcode according to CHIP-8 specification
        '''
        global pc, I, V, stack, sp, memory, gfx, delay_timer, sound_timer, drawflag

        #Fetch opcode
        opcode = memory[pc] << 8 | memory[pc+1]

        #Decode opcode
        decoded = opcode & 0xF000

        #x and y are consant for opcode format.
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4

        #Opcode description on https://en.wikipedia.org/wiki/CHIP-8

        if decoded == 0x0000:
            if opcode == 0x00E0: #00E0
                gfx.surface.fill((0, 0, 0)) #Clears screen
                drawflag = True
                pc += 2
            elif opcode == 0x00EE: #00EE
                pc = stack[sp-1]
                sp -= 1
                pc += 2
        elif decoded == 0x1000:#1NNN
            pc = opcode & 0x0FFF #Obtains last three nibbles
        elif decoded == 0x2000: #2NNN
            stack[sp] = pc
            sp += 1
            pc = opcode & 0x0FFF
        elif decoded == 0x3000: #3XNN:
            if V[x] == opcode & 0x00FF:
                pc += 4
            else:
                pc += 2
        elif decoded == 0x4000: #4XNN:
            if V[x] != opcode & 0x00FF:
                pc += 4
            else:
                pc += 2
        elif decoded == 0x5000: #5XY0:
            if V[x] == V[y]:
                pc += 4
            else:
                pc += 2
        elif decoded == 0x6000: #6XNN
            V[x] = opcode & 0x00FF
            pc += 2
        elif decoded == 0x7000: #7XNN:
            V[x] = V[x] + (opcode & 0x00FF)
            s = opcode & 0x00FF
            if s > 255:
                V[15] = 1
            else:
                V[15] = 0
            pc += 2
        elif decoded == 0x8000:
            #Maps last digit
            last_digit = opcode & 0x000F
            if last_digit == 0x0: #8XY0:
                V[x] = V[y]
                pc += 2
            elif last_digit == 0x1: #8XY1:
                V[x] = V[x] | V[y]
                pc += 2
            elif last_digit == 0x2: #8XY2:
                V[x] = V[x] & V[y]
                pc += 2
            elif last_digit == 0x3: #8XY3:
                V[x] = V[x] ^ V[y]
                pc += 2
            elif last_digit == 0x4: #8XY4:
                s = int(V[x]) + int(V[y])
                V[x] = int(V[x]) + int(V[y])
                if s > 255:
                    V[15] = 1
                else:
                    V[15] = 0
                pc += 2
            elif last_digit == 0x5: #8XY5:
                diff = int(V[x]) - int(V[y])
                V[x] = int(V[x]) - int(V[y])
                if diff < 0:
                    V[15] = 0
                else:
                    V[15] = 1
                pc += 2
            elif last_digit == 0x6: #8XY6:
                lsb = V[x] & 0x1 #least sig bit is last bit
                V[15] = lsb
                V[x] = V[x] >> 1
                pc += 2
            elif last_digit == 0x7: #8XY7:
                diff = int(V[y]) - int(V[x])
                V[x] = int(V[y]) - int(V[x])
                if diff < 0:
                    V[15] = 0
                else:
                    V[15] = 1
                pc += 2
            elif last_digit == 0xE: #8XYE:
                msb = (V[x] & 0xC0) >> 6 #most sig bit
                V[15] = msb
                V[x] = V[x] << 1
                pc += 2
        elif decoded == 0x9000: #9XY0:
            if V[x] != V[y]:
                pc += 4
            else:
                pc += 2
        elif decoded == 0xA000: #ANNN:
            I = opcode & 0x0FFF
            pc += 2
        elif decoded == 0xB000: #BNNN:
            pc = (opcode & 0x0FFF) + V[0]
        elif decoded == 0xC000: #CXNN:
            V[x] = (opcode & 0x00FF) & randint(0, 255)
            pc += 2
        elif decoded == 0xD000: #DXYN:

            #DXYN credit: Rubenknex

            p1 = V[x]
            p2 = V[y]
            height = opcode & 0x000F
            V[15] = 0

            pixel = 0

            for row in range(height):
                for col in range(8):
                    pixel = memory[I+row]

                    if pixel & (0x80 >> col) != 0:
                        pos1 = (p1+col) % 64
                        pos2 = (p2+row) % 32

                        if gfx[pos1, pos2] == 0xFFFFFF:
                            gfx[pos1, pos2] = 0x000000
                            V[15] = 1
                        else:
                            gfx[pos1, pos2] = 0xFFFFFF

            drawflag = True
            pc += 2
        elif decoded == 0xE000:
            last_digit = opcode & 0x000F
            if last_digit == 0xE: #EX9E:
                if keys[V[x]] == 1:
                    pc += 4
                else:
                    pc += 2
            elif last_digit == 0x1: #EXA1:
                if keys[V[x]] == 0:
                    pc += 4
                else:
                    pc += 2
        elif decoded == 0xF000:
            last_digits = opcode & 0x00FF
            if last_digits == 0x07: #FX07:
                V[x] = delay_timer
                pc += 2
            elif last_digits == 0x0A: #FX0A:
                key_press = False
                for i, key in enumerate(keys):
                    #Waits for key press
                    if key == 1:
                        V[x] = i
                        key_press = True #Marks key press

                if key_press == False:
                    pass
                else:
                    pc += 2
            elif last_digits == 0x15: #FX15:
                delay_timer = V[x]
                pc += 2
            elif last_digits == 0x18: #FX18:
                sound_timer = V[x]
                pc += 2
            elif last_digits == 0x1E: #FX1E:
                I = I + V[x]
                pc += 2
            elif last_digits == 0x29: #FX29:
                I = V[x] * 5
                pc += 2
            elif last_digits == 0x33: #FX33:
                #Credit: http://www.multigesture.net/articles/how-to-write-an-emulator-chip-8-interpreter/
                memory[I] = V[x] / 100
                memory[I+1] = (V[x] / 10) % 10
                memory[I+2] = (V[x] % 100) % 10
                pc += 2
            elif last_digits == 0x55: #FX55:
                for i in range(len(V)):
                    if i == x + 1:
                        break
                    memory[I + i] = V[i]
                pc += 2
            elif last_digits == 0x65: #FX65:
                for i in range(len(V)):
                    if i == x + 1:
                        break
                    V[i] = memory[I + i]
                pc += 2


        #Updates timers
        if sound_timer > 0:
            sound_timer -= 1
            if sound_timer == 0:
                print "Beep!"

        if delay_timer > 0:
            delay_timer -= 1

    def setkeys(self):
        '''
        Maps key presses to keys array; original keyboard
        '''
        state = [0 for i in range(16)]

        for event in pygame.event.get():
            #Quits game; ctrl+w
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                #Keydown event
                if event.key == pygame.K_1:
                    state[0] = 1
                elif event.key == pygame.K_2:
                    state[1] = 1
                elif event.key == pygame.K_3:
                    state[2] = 1
                elif event.key == pygame.K_4:
                    state[3] = 1
                elif event.key == pygame.K_q:
                    state[4] = 1
                elif event.key == pygame.K_w:
                    state[5] = 1
                elif event.key == pygame.K_e:
                    state[6] = 1
                elif event.key == pygame.K_r:
                    state[7] = 1
                elif event.key == pygame.K_a:
                    state[8] = 1
                elif event.key == pygame.K_s:
                    state[9] = 1
                elif event.key == pygame.K_d:
                    state[10] = 1
                elif event.key == pygame.K_f:
                    state[11] = 1
                elif event.key == pygame.K_z:
                    state[12] = 1
                elif event.key == pygame.K_x:
                    state[13] = 1
                elif event.key == pygame.K_c:
                    state[14] = 1
                elif event.key == pygame.K_v:
                    state[15] = 1

            keys[0:16] = state #Maps to keys array
