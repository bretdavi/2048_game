#!/usr/bin/env python


"""Python Implementation of 2048"""
__author__ = "Bret Davis"

import sys
import pygame
from pygame.locals import *
import random
import numpy as np
import pprint


SCREEN_SIZE = { 'w' : 640, 'h' : 480 }
BG_COLOR = (104, 94, 85)
FPS = 30
clock = pygame.time.Clock()

class Input(object):
    
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

    pygame.font.init()
    tile_font = pygame.font.Font("Amatic-Bold.ttf", 48)
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

    def __init__(self, x, y, sq_dim=None, val=None):
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

    """TODO: Board on screen is a transposed version of board data
    structure. Need to sort that out....yay
     
    e.g.
    board data struct
    ----------------
    32  0  0  0 
     8  0  0  0 
     0  4 32  0 
     0  0  4  0 

    board on screen
    ----------------
    32  8  0  0
     0  0  4  0
     0  0 32  4
     0  0  0  0
     
    """
    board_color = pygame.Color(173, 160, 133) 
    board_size = { 'w' : 400, 'h' : 400 }
    margins = {'w' : (SCREEN_SIZE['w'] - board_size['w']) / 2,
               'h' : (SCREEN_SIZE['h'] - board_size['h']) / 2}
    gap_size = 10
    num_tiles = 4
    tile_size = (board_size['w'] - ((num_tiles + 1) * gap_size)) / num_tiles

    def __dbg_print(self):
        for i in range(0, self.num_tiles, 1):
            tmp = ""
            for j in range(0, self.num_tiles, 1):
                tmp += str(self._board[i][j].val) + " "
            print tmp
        print


    def __tile_pos(self, tile, x, y):
        """Calculates the tiles corner coordinates based off its index in the 
        board data structure"""

        pos_x = self.margins['w'] + (x * tile.sq_dim) + (self.gap_size * (x + 1))
        pos_y = self.margins['h'] + (y * tile.sq_dim) + (self.gap_size * (y + 1))

        return pos_x, pos_y

    def _board_iter(direction):
        """Given a direction this will yield indices for the row and
        column on each iteration that correspond to iterating in that
        direction.

        For example, if we are iterating from the left, for each row
        iterate the row list from left to right."""

        """Go row by row, and for each row iterate from the left side"""
        print K_LEFT, K_RIGHT, K_DOWN, K_UP
        if direction == K_LEFT:
            for row_i in range(0, self.num_tiles, 1):
                for col_i in range(0, self.num_tiles, 1):
                    yield row_i, col_i

        # Go row by row, and for each row iterate from the right side
        elif direction == K_RIGHT:
            for row_i in range(0, self.num_tiles, 1):
                for col_i in range(self.num_tiles-1, -1, -1):
                    yield row_i, col_i

        # Go column by column, and for each column start from the top
        elif direction == K_UP:
            for col_i in range(0, self.num_tiles, 1):
                for row_i in range(0, self.num_tiles, 1):
                    yield row_i, col_i

        # Go column by column, and for each column start from the bottom
        elif direction == K_DOWN:
            for col_i in range(0, self.num_tiles, 1):
                for row_i in range(self.num_tiles-1, -1, -1):
                    yield row_i, col_i



    def _shift_tiles(self, direction):
        """Given a specific direction, shift all the tiles in the data structure
        to that side of the board"""

        if not direction:
            return

        """1. start with end of row/column in given direction and iterate
           the opposite direction"""

        if direction == K_LEFT:
            for row_i in range(0, self.num_tiles, 1):
                # optimization: Keep track of last tile, don't need to search before that point
                for col_i in range(0, self.num_tiles-1, 1):
                    if self._board[row_i][col_i].val:
                        continue
                    for pos in range(col_i+1,self.num_tiles,1):
                        if self._board[row_i][pos].val:
                            tmp_tile = self._board[row_i][pos]
                            self._board[row_i][pos] = self._board[row_i][col_i]
                            self._board[row_i][col_i] = tmp_tile
                            break

        # Go row by row, and for each row iterate from the right side
        elif direction == K_RIGHT:
             for row_i in range(0, self.num_tiles, 1):
                # optimization: Keep track of last tile, don't need to search before that point
                for col_i in range(self.num_tiles-1, 0, -1):
                    if self._board[row_i][col_i].val:
                        continue
                    for pos in range(col_i-1, -1, -1):
                        if self._board[row_i][pos].val:
                            tmp_tile = self._board[row_i][pos]
                            self._board[row_i][pos] = self._board[row_i][col_i]
                            self._board[row_i][col_i] = tmp_tile
                            break

        # Go column by column, and for each column start from the top
        elif direction == K_UP:
            for col_i in range(0, self.num_tiles, 1):
                for row_i in range(0, self.num_tiles, 1):
                    pass

        # Go column by column, and for each column start from the bottom
        elif direction == K_DOWN:
            for col_i in range(0, self.num_tiles, 1):
                for row_i in range(self.num_tiles-1, -1, -1):
                    pass

        """1.1 Find first empty space in row/column and note it
           EXCEPTION: If no empty spaces, than there is nothing to
           do"""

        """1.2 Find first non-empty space and move to noted empty space
           EXCEPTION: If no non-empty spaces, than there is nothing to do"""

        """REPEAT steps 1.1 and 1.2 until one of the exceptions noted is met"""

    def _merge_tiles(self, direction):
        assert(direction in (K_UP, K_DOWN, K_LEFT, K_RIGHT))

        if direction in (K_UP, K_DOWN):
            for i in range(self._board):
                pass


    def __init__(self, size, init=False):
        self._board = [[None for x in range(size)] for y in range(size)]
        self.size = size
        self.x = (SCREEN_SIZE['w'] - self.board_size['w']) / 2
        self.y = (SCREEN_SIZE['h'] - self.board_size['h']) / 2
        self.board_rect = pygame.Rect(self.x, self.y, self.board_size['w'], self.board_size['h'])

        for i in range(len(self._board)):
            for j in range(len(self._board[i])):
                self._board[i][j] = Tile(i, j, self.tile_size)

        if init:
            o_r1 = -1 
            o_r2 = -1
            for i in range(0,5):
                r1 = random.randint(0, size-1)
                r2 = random.randint(0, size-1)
                while r1 == o_r1 and r2 == o_r2:
                    r1 = random.randint(0, size-1)
                    r2 = random.randint(0, size-1)
                self._board[r1][r2] = Tile(r1, r2, self.tile_size, random.choice([2,4,8,16,32]))
                o_r1 = r1
                o_r2 = r2

        self.__dbg_print()

    def input(self, direction):
        self._shift_tiles(direction)

    def update(self, tiles):
        """Takes a list of tiles and updates the board data structure 
        with said tiles"""

        try:
            for tile in tiles:
                self._board[tile.x][tile.y] = tile
        # if tiles is a single value, just assign it directly
        except TypeError:
            self._board[tiles.x][tiles.y] = tiles

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
        board.input(direction)
        pygame.display.update()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
