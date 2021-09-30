from enum import Enum
import pygame as pg
from random import randint
import json

from settings import *
from very_useful_funcs import *


class CellType(Enum):
    border = 0,
    snake = 1,
    food = 2,
    empty = 3


int_to_cell_type = {
    0: CellType.border,
    1: CellType.snake,
    2: CellType.food,
    3: CellType.empty,
}


class Cell:
    food_cells = []
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
        all_c = cls.food_cells + cls.border_cells
        for s in Snake.snakes:
            all_c += s.cells

        return all_c

    @classmethod
    def get_type_cells(cls, c_type=CellType.empty) -> list:
        if c_type == CellType.food:
            return cls.food_cells
        if c_type == CellType.border:
            return cls.border_cells
        if c_type == CellType.snake:
            return open_list([s.cells for s in Snake.snakes])
        return []

    @classmethod
    def add_cell(cls, cell):
        if cell.type == CellType.border:
            cls.border_cells += [cell]
        elif cell.type == CellType.food:
            cls.food_cells += [cell]


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
                    s += [Sensor((x, y), tuple([randint(-5, 5) for i in range(4)]), s_type)]

                    if s_type in (CellType.border, CellType.snake, CellType.food):
                        if x == -1 and y == 0:
                            s[-1].values = (5, 11, 5, -11)
                        elif x == 1 and y == 0:
                            s[-1].values = (5, -11, 5, 11)
                        elif x == 0 and y == 1:
                            s[-1].values = (11, 5, -11, 5)
                        elif x == 0 and y == -1:
                            s[-1].values = (-11, 5, 11, 5)

                        if s_type == CellType.food:
                            s[-1].values = mult_tuple_int(s[-1].values, -1)

        return tuple(s)

    @classmethod
    def generate_all(cls, sz: int) -> tuple:
        s = ()
        for i in CellType:
            if i == CellType.empty:
                continue
            s = s + cls.generate(sz, i)
        return s

    @staticmethod
    def make_error(sens: tuple, n: int) -> None:
        for _ in range(n):
            s = sens[randint(0, len(sens) - 1)]
            sv = list(s.values)
            j = randint(0, 3)
            sv[j] = min(64, max(-64, sv[j] + randint(-10, 10)))
            s.values = tuple(sv)

    def __init__(self, pos: tuple, values: tuple, cell_type=CellType.empty):
        self.pos = pos
        self.type = cell_type
        self.values = values

    def view(self, d_pos: tuple) -> tuple:
        c = Cell.find_cell_pos(Cell.get_type_cells(self.type), sum_tuple(d_pos, self.pos))
        return self.values if c and c.type == self.type else (0, 0, 0, 0)


class Snake:
    snakes = []

    health_in_food = 40

    @classmethod
    def generate_snake(cls, pos: tuple, dir_=Dirs.down, l_=4, sensors=()):
        c = []
        for i in range(l_):
            c += [Cell(pos, CellType.snake)]
            pos = sum_tuple(pos, dirs_dirs[dir_])

        return Snake(c, sensors if sensors else Sensor.generate_all(3))

    @classmethod
    def update_all(cls):
        i = 0
        while i < len(cls.snakes):
            if cls.snakes[i].update():
                i += 1

    def __init__(self, cells: list, sensors: tuple, steps=0):
        self.cells = cells
        self.sensors = sensors
        self.health = Snake.health_in_food * 2

        self.life_steps = 0

        Snake.snakes += [self]

    def __del__(self):
        if self in Snake.snakes:
            Snake.snakes.remove(self)

    def move(self, pos):
        for i in range(len(self.cells) - 1, 0, -1):
            self.cells[i].pos = self.cells[i - 1].pos

        self.cells[0].pos = pos

    def die(self):
        Logger.on_snake_death(self)

        self.cells = []

        Snake.snakes.remove(self)

    def eat(self, pos):
        tail = self.cells[-1].pos
        Cell.food_cells.remove(Cell.find_cell_pos(Cell.food_cells, pos))
        self.move(pos)
        self.cells += [Cell(tail, CellType.snake)]

        if len(self.cells) >= 10:
            self.replication()

    def replication(self):
        s = self.cells[len(self.cells) // 2:][::-1]
        self.cells = self.cells[:len(self.cells) // 2]

        sn = Snake(s, self.sensors, steps=self.life_steps)
        if not randint(0, 3):
            Sensor.make_error(sn.sensors, randint(1, 5))

        self.health = sn.health

    def cut_tail(self) -> bool:
        self.health = self.health_in_food

        self.cells.pop(-1)
        if len(self.cells) < 4:
            self.die()
            return False

        return True

    def go(self, dir_) -> bool:

        pos = self.cells[0].pos
        pos = sum_tuple(pos, dirs_dirs[dir_])

        c = Cell.find_cell_pos(Cell.get_all_cells(), pos)

        if c.__class__ == Cell:
            if c.type == CellType.food:
                self.eat(pos)
            elif c.type in (CellType.border, CellType.snake):
                self.die()
                return False
        else:
            self.move(pos)

        self.health -= 1
        if self.health <= 0 and not self.cut_tail():
            return False

        self.life_steps += 1

        return True

    def update(self) -> bool:
        sum_ = (0, 0, 0, 0)
        for i in self.sensors:
            sum_ = sum_tuple(sum_, i.view(self.cells[0].pos))

        return self.go(Sensor.dirs[sorted(enumerate(sum_), key=lambda x: -x[1])[0][0]])


class Field:
    food_n = n_w_cells * 2

    @staticmethod
    def gen_borders():
        for x in range(0, n_w_cells):
            Cell.add_cell(Cell((x, 0)))
            Cell.add_cell(Cell((x, n_h_cells - 1)))

        for y in range(0, n_h_cells):
            Cell.add_cell(Cell((0, y)))
            Cell.add_cell(Cell((n_w_cells - 1, y)))

    @staticmethod
    def generate_food():
        while len(Cell.food_cells) < Field.food_n:
            pos = randint(1, n_w_cells - 2), randint(1, n_h_cells - 2)
            while Cell.find_cell_pos(Cell.get_all_cells(), pos):
                pos = randint(1, n_w_cells - 2), randint(1, n_h_cells - 2)

            Cell.add_cell(Cell(pos, CellType.food))


class Drawer:
    colors = {
        CellType.border: border_color,
        CellType.food: eat_color,
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


class Logger:
    @staticmethod
    def sensors_to_list(t: tuple):
        r = []
        for i in t:
            r += [{
                    "pos": i.pos,
                    "val": i.values,
                    "typ": i.type.value[0]
                }]

        return r

    @staticmethod
    def list_to_sensors(t: list):
        r = []
        for i in t:
            r += [Sensor(tuple(i["pos"]), tuple(i["val"]), int_to_cell_type[i["typ"]])]

        return tuple(r)

    @staticmethod
    def on_snake_death(snake: Snake):
        js = json.load(open("genes.json", encoding="UTF-8"))

        js["history"] += [snake.life_steps]

        if js["best"]["score"] <= snake.life_steps:
            js["best"]["score"] = snake.life_steps
            js["best"]["genes"] = Logger.sensors_to_list(snake.sensors)

        open("genes.json", 'w', encoding="UTF-8").write(json.dumps(js))

    @staticmethod
    def get_best_snake_sens():
        return Logger.list_to_sensors(json.load(open("genes.json", encoding="UTF-8"))["best"]["genes"])

    @staticmethod
    def clear_json():
        if json.load(open("genes.json", encoding="UTF-8"))["need_del"]:
            open("genes.json", 'w', encoding="UTF-8").write(json.dumps({
                "need_del": False,
                "best": {
                    "score": -1,
                    "genes": []
                },
                "history": []
            }))


Logger.clear_json()

pg.init()
sc = pg.display.set_mode(size)

pg.display.set_caption('Snakes')

clock = pg.time.Clock()

Field.gen_borders()


while True:
    sc.fill(bg_color)
    for event in pg.event.get():
        if event.type == pg.QUIT:
            exit(0)

    if len(Snake.snakes) == 0:
        Cell.food_cells = []
        for x in range(10):
            for y in range(9):
                s = Snake.generate_snake((16 + x * 4, 3 + y * 6), sensors=Logger.get_best_snake_sens())
                if x % 2:
                    Sensor.make_error(s.sensors, randint(1, 5))

    Field.generate_food()

    Snake.update_all()

    Drawer.draw_cells(Cell.get_all_cells())
    Drawer.draw_lines()

    pg.display.flip()
    clock.tick(1000)




