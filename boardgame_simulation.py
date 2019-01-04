from collections import Counter
import pandas as pd
from random import shuffle
from string import ascii_uppercase as letters


class SharedBoard:
    def __init__(self):
        self.n = 100
        self.m = 8
        self.c = 5

        self.players = 4

        self.tile_space = list(letters[:self.c])
        self.tiles = self.tile_space * int(self.n / self.c)
        shuffle(self.tiles)

        self.pouch = list(self.tiles)
        self.plates = None

        self.middle = Counter()

        self.draw_tiles()
        pass

    def draw_tiles(self):
        n = 4
        z = int(self.m * n)

        self.plates = [Counter(self.pouch[i:i+n]) for i in range(0, z, n)]
        pass


class PlayerBoard:
    def __init__(self, limit_final_field=True):
        self.preset = limit_final_field
        self.pool = Counter()  # just a pool of tiles, unordered.

        self.round_field = [(i, Counter()) for i in range(1, 6)]
        self.final_field_check = self.setup_final_field()
        self.final_field = pd.DataFrame(0,
                                        index=range(1, 6),
                                        columns=range(1, 6))

        self.minus_field = [-1, -1, -2, -2, -2, -3, -3]

        self.point_total = 0

    def endround_points(self):
        pass

    def endgame_points(self):
        pass

    def setup_final_field(self):
        if self.preset:
            values = 'ABCDE' * 2
            valid_list = [list(values[i:i+5]) for i in range(5)]
        else:
            values = 'ABCDE'
            valid_list = [set(list(values)) for _ in range(5)]
        return pd.DataFrame(valid_list)


shared_board = SharedBoard()


class Player:
    def __init__(self):
        self.own_board = PlayerBoard()
        pass

    def draw_from_plate(self, tile, plate):
        """
        Draws tiles from the shared board and adds them to player board.
        The remaining tiles are added to the shared board's middle.

        :param tile: str, 'A' - 'E'
        :param plate: int, plate identifier in range(8)
        """
        tile = str(tile)
        counter = shared_board.plates[plate]
        if counter[tile] == 0:
            msg = f'Plate {plate} does not contain tile {tile}. ' \
                  f'Plate {plate} consists of {shared_board.plates[plate]}'
            raise ValueError(msg)

        shared_board.plates[plate] = Counter()  # empty the plate

        to_player = Counter({tile: counter[tile]})
        to_middle = counter - to_player

        shared_board.middle += to_middle
        self.own_board.pool += to_player
        pass

    def draw_from_middle(self, tile):
        tile = str(tile)

        to_player = shared_board.middle[tile]
        if to_player == 0:
            msg = f'There is no tile {tile} in the middle.' \
                  f'The middle consists of {shared_board.middle}'
            raise ValueError(msg)

        shared_board.middle -= to_player
        self.own_board.pool += to_player
        pass

    def add_to_round_field(self):
        pass


luke = Player()
ken = Player()
shared_board.plates

luke.draw_from_plate('A', 0)
shared_board.plates