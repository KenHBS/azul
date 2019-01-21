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


MIDDLE = SharedBoard()


class Player:
    def __init__(self, player_name, limit_final_field=True):
        self.name = player_name

        self.preset = limit_final_field
        self.pool = Counter()  # just a pool of tiles, unordered.

        self.round_field = [(i, Counter()) for i in range(1, 6)]
        self.final_field_check = self.setup_final_field()
        self.final_field = pd.DataFrame(0,
                                        index=range(1, 6),
                                        columns=range(1, 6))

        self.minus_field = [-1, -1, -2, -2, -2, -3, -3]

        self.round_minus = self.minus_field.copy()

        self.min_counts = 0
        self.point_total = 0

    def endround_points(self):
        round_plus = self.move_to_final_field()
        round_minus = self.min_counts

        round_points = round_plus + round_minus
        self.point_total += round_points

        msg = 'You earned {} points this round. Your total is {}'
        msg = msg.format(round_points, self.point_total)
        print(msg)

        self.min_counts = 0

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

    @property
    def final_field_dummy(self):
        """ this property is used for counting the fields """
        is_not_null = ~self.final_field.isnull()
        return is_not_null * 1

    def start_new_round(self):
        pass

    def move_to_final_field(self):
        if not self.preset:
            msg = 'Populating final field is not yet implemented for the' \
                  'non-preset final field. Use "limit_final_preset=True" ' \
                  'instead'
            raise NotImplementedError(msg)

        round_points = 0
        for row, (cap, counter) in enumerate(self.round_field):
            grid = self.final_field_check

            tile, count = get_kind_and_count(counter)

            #  if the round field is completely full
            if cap == count:
                m = pd.Index(grid.iloc[row])
                col = m.get_loc(tile)

                self.final_field.loc[row, col] = tile

                #  empty the round field
                self.round_field[row] = (cap, Counter())

                #  count the points for that tile
                tile_points = self.count_tile_value(row, col)
                round_points += tile_points

        return round_points

    def count_tile_value(self, row, col):
        """ calculate the points caused by turning cell (row, col) to 1 """
        _col = self.final_field_dummy[col]
        _row = self.final_field_dummy.loc[row]

        count = 1
        for i in reversed(range(0, row)):
            if _col[i] == 1:
                count += 1
            else:
                break
        for i in range(row, 6):
            if _col[i] == 1:
                count += 1
            else:
                break
        for j in reversed(range(0, col)):
            if _row[j] == 1:
                count += 1
            else:
                break
        for j in range(col, 6):
            if _row[j] == 1:
                count += 1
            else:
                break
        return count


def draw_from_plate(tile, plate):
    """
    Draws tiles from the shared board and adds them to player board.
    The remaining tiles are added to the shared board's middle.

    :param tile: str, 'A' - 'E'
    :param plate: int, plate identifier in range(8)
    """
    tile = str(tile)
    counter = MIDDLE.plates[plate]
    if counter[tile] == 0:
        msg = f'Plate {plate} does not contain tile {tile}. ' \
              f'Please choose another tile or another plate:' \
              f'Plate {plate} consists of {MIDDLE.plates[plate]}'
        raise ValueError(msg)

    MIDDLE.plates[plate] = Counter()  # empty the plate

    to_player = Counter({tile: counter[tile]})
    to_middle = counter - to_player

    MIDDLE.middle += to_middle

    chosen_tiles = to_player
    return chosen_tiles


def draw_from_middle(tile):
    tile = str(tile)

    to_player = MIDDLE.middle[tile]
    if to_player == 0:
        msg = f'There is no tile {tile} in the middle.' \
              f'The middle consists of {MIDDLE.middle}'
        raise ValueError(msg)

    MIDDLE.middle -= to_player

    chosen_tiles = to_player
    return chosen_tiles


def get_kind_and_count(counter):
    """"returns the first -and only!- (key, value) pair"""
    try:
        key, value = list(counter.items())[0]
    except IndexError:
        key, value = (None, None)
    return key, value


def handle_slots_exceeded(player, avail, attempt, kind):
    diff = attempt - avail
    minus = 0
    for _ in range(diff):
        try:
            minus += player.round_minus.pop(0)
        except IndexError:
            minus = -14
            msg = 'You exceeded the minus point cap of -14 per round'
            print(msg)

    player.min_counts += minus

    msg = '{} too many tiles for this row. This will give you {} minus'
    msg = msg.format(diff, minus)
    print(msg)

    _counter = Counter({kind: avail})
    return _counter


def add_to_round_field(player, row, chosen_tiles):
    """
    Check validity and carry out move.
    Check validity in two ways:
    1) See if no other tile type is already occupying the row
    2) See if the max. number of slots will be exceeded, if so, then

    :param player: Player instance
    :param row: int, row number in range(0, 5)
    :param chosen_tiles: Counter() with one key-value pair
    :return:
    """
    max_slots, old_counter = player.round_field[int(row)]

    old_kind, old_count = get_kind_and_count(old_counter)
    add_kind, add_count = get_kind_and_count(chosen_tiles)

    new_counter = old_counter + chosen_tiles
    new_kind, new_count = get_kind_and_count(new_counter)

    if len(new_counter) > 1:
        msg = 'Cannot add {} here, since it already contains {} time(s) {}'
        err = msg.format(add_kind, old_kind, old_count)
        raise ValueError(err)

    if new_count > max_slots:
        new_counter = handle_slots_exceeded(player, max_slots, new_count, new_kind)

    player.round_field[int(row)] = new_counter
    pass


def print_plate_state():
    for i, plate in enumerate(MIDDLE.plates):
        if len(plate) > 0:
            print(' Plate {i} contains: \n')
            for tile, count in plate.items():
                msg = f'   {count} times {tile} \n'
                print(msg)
    pass


def print_middle_state():
    if len(MIDDLE.middle) > 0:
        print('\n The middle contains: \n')
        for tile, count in MIDDLE.middle.items():
            msg = f'   {count} times {tile}'
            print(msg)
    else:
        print(' The middle is empty')
    pass


def print_own_field(round_field):
    for i, counter in enumerate(round_field):
        tile, count = get_kind_and_count(counter)
        if count is None:
            count = 0
        filled_tiles = f'[{tile}] ' * count
        empty_tiles = f'[ ] ' * (i + 1 - count)
        line = filled_tiles + empty_tiles
        print(line)
    pass



luke = Player(name='Luke')
ken = Player(name='Ken')

player_names = ['Luke', 'Paula', 'Emil', 'Inga']
players = [Player(name=name) for name in player_names]

#draw = draw_from_plate('C', 0)
#add_to_round_field(luke, 0, draw)


#draw = draw_from_plate('B', 0)
# TODO: Simulate a game:
# while not_empty(middle, plates):
#   do moves
# move_to_final_field, count points, etc.
#


player_nr = 0
current_player = players[player_nr]

tiles_left = True
while tiles_left:

    print_plate_state()
    print_middle_state()
    print('---')
    print(f"{current_player.name}, it's your turn.. ")

    print(f'Your plate looks like: \n')
    print_own_field(current_player.round_field)

    plate_nr = input('Which plate would you like to draw from? \n > ')
    tile_type = input('And which tile would you like to take? \n > ')

    draw = draw_from_plate(tile_type, plate_nr)


    empty_middle = (len(MIDDLE.middle) == 0)
    empty_plates = all(len(plate) == 0 for plate in MIDDLE.plates)
    tiles_left = ~(empty_middle & empty_plates)

    player_nr += 1
    try:
        current_player = players[player_nr]
    except IndexError:
        player_nr = 0
        current_player = players[player_nr]


