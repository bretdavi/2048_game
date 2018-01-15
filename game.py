#!/usr/bin/env python


"""Python Implementation of 2048"""
__author__ = "Bret Davis"

import sys
import time
import pygame
from pygame.locals import *
import random
import pprint
import copy


SCREEN_SIZE = { 'w' : 640, 'h' : 480 }
BG_COLOR = (104, 94, 85)
FPS = 30
clock = pygame.time.Clock()

class Input(object):
    """Simple class to wrap the handling of user input.

    Currently, check_input is the only method, which returns
    K_LEFT, K_RIGHT, K_UP, or K_DOWN corresponding to the arrow
    and wasd keys. It will also quit if the window is closed or
    the escape key is pressed.

    Since the only method is a classmethod, an object from this
    class is never instantiated
    """

    @classmethod
    def check_input(inp):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYUP:
                if event.key in (K_LEFT, K_a): return K_LEFT
                if event.key in (K_RIGHT, K_d): return K_RIGHT
                if event.key in (K_DOWN, K_s): return K_DOWN
                if event.key in (K_UP, K_w): return K_UP

                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

class Tile(object):
    """This represents the numbered or blank tiles that appear
    on the game board.

    The Tile class tracks the font used by the tiles, the pixel
    dimensions of the tiles, and the different tile background
    colors.
    """
    
    pygame.font.init()
    tile_font = pygame.font.Font("Amatic-Bold.ttf", 48)
    #                   R    G   B
    bg_tile_color =   (130, 119, 98)
    colors = { 2    : (165, 225, 229),
               4    : ( 94, 167, 178),
               8    : ( 93, 145, 178),
               16   : ( 93, 121, 178),
               32   : ( 95,  93, 178),
               64   : (121,  84, 173),
               128  : (181,  82, 211),
               256  : (232,  85, 212),
               512  : (232, 148, 148),
               1024 : (255,  84,  84),
               2048 : (234, 138,  49)}   

    sq_dim = 64

    def __eq__(self, other):
        """Overrides equality operator (==) for the Tile class.

        When comparing two tile objects, (e.g. Tile1 == Tile2)
        this will compare the tile value, rather than the Object
        reference
        """
        if isinstance(self, other.__class__):
            return self.val == other.val
        return NotImplemented

    def __ne__(self, other):
        """Overrides the inequality operator (!=) for the Tile class

        inverse of the equality operator above
        """
        if isinstance(self, other.__class__):
            return self.val != other.val
        return NotImplemented

    def __init__(self, sq_dim=None, val=None):
        """A Tile object stores its graphical attributes and
        data values

        The tile has a numerical value, or None, which indicates a 
        background tile. The color of the tile is based on the tile's
        value.

        Args:
            sq_dim (int): number of pixels per tile side. If left blank
                the class default value is used,
            val    (int): The numerical value of the tile. If left blank,
                the tile is set to None, making it a blank background tile
        
        """
        self.val = val
        self.txt = str(val) if val else ""
        if sq_dim: self.sq_dim = sq_dim
        if val:
            self.color = self.colors[val]
        else:
            self.color = self.bg_tile_color
        self.text_obj = self.tile_font.render(self.txt, True, (255,255,255))

    def draw(self, screen, pix_x, pix_y):
        self.tile_rect = pygame.Rect(pix_x, pix_y, self.sq_dim, self.sq_dim)
        pygame.draw.rect(screen, self.color, self.tile_rect)
        text_rect = self.text_obj.get_rect()
        text_x = pix_x + (self.sq_dim / 2)
        text_y = pix_y + (self.sq_dim / 2)
        text_rect.center = (text_x, text_y)
        screen.blit(self.text_obj, text_rect)

    def __str__(self):
        return str(self.val)


class Board(object):

    board_color = pygame.Color(173, 160, 133) 
    board_size = { 'w' : 400, 'h' : 400 }
    margins = {'w' : (SCREEN_SIZE['w'] - board_size['w']) / 2,
               'h' : (SCREEN_SIZE['h'] - board_size['h']) / 2}
    gap_size = 10
    # Distribution of tiles for new tile creation
    new_tiles = [2,2,2,2,2,2,4]

    def __dbg_print(self):
        for i in range(0, self.size, 1):
            tmp = ""
            for j in range(0, self.size, 1):
                tmp += str(self._board[i][j].val) + " "
            print tmp
        print


    def __tile_pos(self, tile, x, y):
        """Calculates the tiles corner coordinates based off its index in the 
        board data structure"""

        pos_x = self.margins['w'] + (x * tile.sq_dim) + (self.gap_size * (x + 1))
        pos_y = self.margins['h'] + (y * tile.sq_dim) + (self.gap_size * (y + 1))

        return pos_x, pos_y


    def _update_tiles(self, direction, board=None):
        """Given a specific direction, shift all the tiles in the data structure
        to that side of the board"""

        # Set to true if the input changes the board state
        updated = False
        if not board:
            board = self._board

        if not direction:
            return updated

        if direction == K_LEFT:
            # Merge any possible tiles
            for row_i in range(0, self.size, 1):
                for col_i in range(0, self.size-1, 1):
                    if not board[row_i][col_i].val:
                        continue

                    for pos in range(col_i+1,self.size,1):
                        if board[row_i][pos] == board[row_i][col_i]:
                            board[row_i][pos] = Tile(self.tile_size, None)
                            board[row_i][col_i] = Tile(self.tile_size, board[row_i][col_i].val*2)
                            updated = True
                            break
                        # If tile didn't match and isn't any empty space stop checking
                        elif board[row_i][pos].val != None:
                            break

            # Shift all tiles to the Left
            for row_i in range(0, self.size, 1):
                for col_i in range(0, self.size-1, 1):
                    if board[row_i][col_i].val:
                        continue

                    for pos in range(col_i+1,self.size,1):
                        if board[row_i][pos].val:
                            tmp_tile = board[row_i][pos]
                            board[row_i][pos] = board[row_i][col_i]
                            board[row_i][col_i] = tmp_tile
                            updated = True
                            break


        # Go row by row, and for each row iterate from the right side
        elif direction == K_RIGHT:
            # Merge any possible tiles
            for row_i in range(0, self.size, 1):
                for col_i in range(self.size-1, 0, -1):
                    if not board[row_i][col_i].val:
                        continue

                    for pos in range(col_i-1, -1, -1):
                        if board[row_i][pos] == board[row_i][col_i]:
                            board[row_i][pos] = Tile(self.tile_size, None)
                            board[row_i][col_i] = Tile(self.tile_size, board[row_i][col_i].val*2)
                            updated = True
                            break
                        # If tile didn't match and isn't any empty space stop checking
                        elif board[row_i][pos].val != None:
                            break

            # Shift all tiles to Right
            for row_i in range(0, self.size, 1):
                for col_i in range(self.size-1, 0, -1):
                    if board[row_i][col_i].val:
                        continue

                    for pos in range(col_i-1, -1, -1):
                        if board[row_i][pos].val:
                            tmp_tile = board[row_i][pos]
                            board[row_i][pos] = board[row_i][col_i]
                            board[row_i][col_i] = tmp_tile
                            updated = True
                            break

        # Go column by column, and for each column start from the top
        elif direction == K_UP:
            # Merge tiles
            for col_i in range(0, self.size, 1):
                for row_i in range(0, self.size-1, 1):
                    if not board[row_i][col_i].val:
                        continue

                    for pos in range(row_i+1,self.size,1):
                        if board[pos][col_i] == board[row_i][col_i]:
                            board[pos][col_i] = Tile(self.tile_size, None)
                            board[row_i][col_i] = Tile(self.tile_size, board[row_i][col_i].val*2)
                            updated = True
                            break
                        # If tile didn't match and isn't any empty space stop checking
                        elif board[pos][col_i].val != None:
                            break

            # Shift tiles up
            for col_i in range(0, self.size, 1):
                for row_i in range(0, self.size-1, 1):
                    if board[row_i][col_i].val:
                        continue

                    for pos in range(row_i+1,self.size,1):
                        if board[pos][col_i].val:
                            tmp_tile = board[pos][col_i]
                            board[pos][col_i] = board[row_i][col_i]
                            board[row_i][col_i] = tmp_tile
                            updated = True
                            break

        # Go column by column, and for each column start from the bottom
        elif direction == K_DOWN:
            # Merge tiles
            for col_i in range(0, self.size, 1):
                for row_i in range(self.size-1, 0, -1):
                    if not board[row_i][col_i].val:
                        continue

                    for pos in range(row_i-1, -1, -1):
                        if board[pos][col_i] == board[row_i][col_i]:
                            board[pos][col_i] = Tile(self.tile_size, None)
                            board[row_i][col_i] = Tile(self.tile_size, board[row_i][col_i].val*2)
                            updated = True
                            break
                        # If tile didn't match and isn't any empty space stop checking
                        elif board[pos][col_i].val != None:
                            break
            # Shift tiles down
            for col_i in range(0, self.size, 1):
                for row_i in range(self.size-1, 0, -1):
                    if board[row_i][col_i].val:
                        continue

                    for pos in range(row_i-1, -1, -1):
                        if board[pos][col_i].val:
                            tmp_tile = board[pos][col_i]
                            board[pos][col_i] = board[row_i][col_i]
                            board[row_i][col_i] = tmp_tile
                            updated = True
                            break
        return updated


    def __init__(self, size, init=False):
        self._board = [[None for x in range(size)] for y in range(size)]
        self.size = size
        self.tile_size = (self.board_size['w'] - ((size + 1) * self.gap_size)) / size
        self.x = (SCREEN_SIZE['w'] - self.board_size['w']) / 2
        self.y = (SCREEN_SIZE['h'] - self.board_size['h']) / 2
        self.board_rect = pygame.Rect(self.x, self.y, self.board_size['w'], self.board_size['h'])

        for i in range(len(self._board)):
            for j in range(len(self._board[i])):
                self._board[i][j] = Tile(self.tile_size)

        if init:
                self.add_rand_tile([2])
                self.add_rand_tile([2])

        self.__dbg_print()

    def update_game(self, direction, screen):
        game_over = True
        updated = self._update_tiles(direction)
        won = self.check_for_win(screen)
        lost = self.check_for_loss(screen)
        if won or lost:
            return game_over

        if updated:
            self.add_rand_tile()

        return False

    def _result_animation(self, screen, text):
        pygame.font.init()
        res_font = pygame.font.Font("Amatic-Bold.ttf", 128)
        text_obj = res_font.render(text, True, (240,255,255))
        res_rect = text_obj.get_rect()

        text_x = SCREEN_SIZE['w'] / 2
        text_y = SCREEN_SIZE['h'] / 2
        res_rect.center = (text_x, text_y)

        screen.blit(text_obj, res_rect)

    def check_for_win(self, screen):
        for x in range(0, self.size):
            for y in range(0, self.size):
                if self._board[x][y].val == 2048:
                    self._result_animation(screen, "You Win!")
                    return True
        return False

    def check_for_loss(self, screen):
        test_board = copy.deepcopy(self._board)
        loss = not self._update_tiles(K_LEFT, test_board)
        loss &= not self._update_tiles(K_RIGHT, test_board)
        loss &= not self._update_tiles(K_UP, test_board)
        loss &= not self._update_tiles(K_DOWN, test_board)

        if loss:
            self._result_animation(screen, "You SUCK!")
        return loss

    def add_rand_tile(self, val_list=None):
        x = random.randint(0, self.size - 1)
        y = random.randint(0, self.size - 1)
        
        if not val_list:
            val_list = self.new_tiles

        val = random.choice(val_list)

        while self._board[x][y].val:
            x = random.randint(0, self.size - 1)
            y = random.randint(0, self.size - 1)

        self._board[x][y] = Tile(self.tile_size, val)

    def draw(self, screen):
        """Draws the game board to the display"""

        pygame.draw.rect(screen, self.board_color, self.board_rect, 1)

        # Need to transform array due to differences in data structure
        # and screen coordinates
        trans_board = zip(*self._board)
        for i in range(len(trans_board)):
            for j in range(len(trans_board[i])):
                tile = trans_board[i][j]
                pos_x, pos_y = self.__tile_pos(tile, i, j)
                tile.draw(screen, pos_x, pos_y)


def main():

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_SIZE['w'], SCREEN_SIZE['h']))
    pygame.display.set_caption('2048')
    screen.fill(BG_COLOR)
    board = Board(4, init=True)

    while True:
        board.draw(screen)
        direction = Input.check_input()
        game_over = board.update_game(direction, screen)
        pygame.display.update()
        if game_over:
            while True:
                Input.check_input()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
