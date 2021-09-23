from enum import Enum
import pygame as pg
from random import randint

from settings import *
from very_useful_funcs import *


class CellType(Enum):
    border = 0,
    snake = 1,
    eat = 2,
    empty = 3


class Cell:
    eat_cells = []
    border_cells = []

    def __init__(self, pos: tuple, cell_type=CellType.border):
        self.type = cell_type
        self.pos = pos

    @staticmethod
    def find_cell_pos(cells: list, pos: tuple):
        for c in cells:
            if c.pos == pos:
                return c

        return None

    @classmethod
    def get_all_cells(cls) -> list:
        all_c = cls.eat_cells + cls.border_cells
        for s in Snake.snakes:
            all_c += s.cells

        return all_c

    @classmethod
    def add_cell(cls, cell):
        if cell.type == CellType.border:
            cls.border_cells += [cell]
        elif cell.type == CellType.eat:
            cls.eat_cells += [cell]


class Dirs(Enum):
    up = 0,
    down = 1,
    right = 2,
    left = 3


dirs_dirs = {
    Dirs.up: (0, -1),
    Dirs.down: (0, 1),
    Dirs.right: (1, 0),
    Dirs.left: (-1, 0)
}


class Sensor:
    dirs = (Dirs.up, Dirs.right, Dirs.down, Dirs.left)

    @classmethod
    def generate(cls, sz: int, s_type=CellType.empty) -> tuple:
        s = []
        for x in range(-sz, sz):
            for y in range(-sz, sz):
                if not (x == y == 0):
                    s += [Sensor((x, y), tuple([randint(-64, 64) for i in range(4)]), s_type)]
        return tuple(s)

    @classmethod
    def generate_all(cls, sz: int) -> tuple:
        s = ()
        for i in CellType:
            s = s + cls.generate(sz, i)
        return s

    def __init__(self, pos: tuple, values: tuple, cell_type=CellType.empty):
        self.pos = pos
        self.type = cell_type
        self.values = values

    def view(self, d_pos: tuple) -> tuple:
        c = Cell.find_cell_pos(Cell.get_all_cells(), sum_tuple(d_pos, self.pos))
        return self.values if c and c.type == self.type else (0, 0, 0, 0)


class Snake:
    snakes = []

    @classmethod
    def generate_snake(cls, pos: tuple, dir_=Dirs.down, l_=4):
        c = []
        for i in range(l_):
            c += [Cell(pos, CellType.snake)]
            pos = sum_tuple(pos, dirs_dirs[dir_])

        return Snake(c, Sensor.generate_all(1))

    @classmethod
    def update_all(cls):
        i = 0
        while i < len(cls.snakes):
            if cls.snakes[i].update():
                i += 1

    def __init__(self, cells: list, sensors: tuple):
        self.cells = cells
        self.sensors = sensors

        Snake.snakes += [self]

    def __del__(self):
        if self in Snake.snakes:
            Snake.snakes.remove(self)

    def move(self, pos):
        for i in range(len(self.cells) - 1, 0, -1):
            self.cells[i].pos = self.cells[i - 1].pos

        self.cells[0].pos = pos

    def die(self):
        for c in self.cells:
            c.type = CellType.eat
            Cell.add_cell(c)

        Snake.snakes.remove(self)

    def eat(self, pos):
        tail = self.cells[-1].pos
        Cell.eat_cells.remove(Cell.find_cell_pos(Cell.eat_cells, pos))
        self.move(pos)
        self.cells += [Cell(tail, CellType.snake)]

        if len(self.cells) >= 10:
            self.replication()

    def replication(self):
        s = self.cells[len(self.cells) // 2:][::-1]
        self.cells = self.cells[:len(self.cells) // 2]

        Snake(s, self.sensors)

    def go(self, dir_) -> bool:
        f = True

        pos = self.cells[0].pos
        pos = sum_tuple(pos, dirs_dirs[dir_])

        c = Cell.find_cell_pos(Cell.get_all_cells(), pos)

        if c.__class__ == Cell:
            if c.type == CellType.eat:
                self.eat(pos)
            elif c.type in (CellType.border, CellType.snake):
                self.die()
                f = False
        else:
            self.move(pos)

        return f

    def update(self) -> bool:
        sum_ = (0, 0, 0, 0)
        for i in self.sensors:
            sum_ = sum_tuple(sum_, i.view(self.cells[0].pos))

        return self.go(Sensor.dirs[sorted(enumerate(sum_), key=lambda x: -x[1])[0][0]])


class Field:
    @staticmethod
    def gen_borders():
        for x in range(0, n_w_cells):
            Cell.add_cell(Cell((x, 0)))
            Cell.add_cell(Cell((x, n_h_cells - 1)))

        for y in range(0, n_h_cells):
            Cell.add_cell(Cell((0, y)))
            Cell.add_cell(Cell((n_w_cells - 1, y)))


class Drawer:
    colors = {
        CellType.border: border_color,
        CellType.eat: eat_color,
        CellType.snake: snake_color,
    }

    @staticmethod
    def draw_lines():
        for x in range(1, n_w_cells):
                pg.draw.rect(sc, line_color, (x * cell_size, 0, 1, height))

        for y in range(1, n_h_cells):
                pg.draw.rect(sc, line_color, (0, y * cell_size, width, 1))

    @staticmethod
    def draw_cells(cells: list, color=()):
        for c in cells:
            pg.draw.rect(sc, color if color else Drawer.colors.get(c.type, error_color),
                         (c.pos[0] * cell_size, c.pos[1] * cell_size, cell_size, cell_size))


pg.init()
sc = pg.display.set_mode(size)

pg.display.set_caption('Snakes')

clock = pg.time.Clock()

Field.gen_borders()


for x in range(45):
    Snake.generate_snake((4 + x * 2, 30), Dirs.down)
    Snake.generate_snake((4 + x * 2, 31))

# for y in range(20):
#     Cell.add_cell(Cell((10, 10 + y), CellType.eat))


while True:
    sc.fill(bg_color)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit(0)
        elif event.type == pg.MOUSEMOTION:
            pass

    Snake.update_all()

    Drawer.draw_cells(Cell.get_all_cells())
    Drawer.draw_lines()

    pg.display.flip()
    clock.tick(10)




