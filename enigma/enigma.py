import numpy as np
from numpy.random import default_rng
import string


def gen_permutor_lists(n_elements, seed):
    elements = range(n_elements)
    rng = default_rng(seed)
    perm_forward = rng.permutation(elements).tolist()
    perm_backward = [perm_forward.index(el) for el in elements]

    return perm_forward, perm_backward


def gen_swap_dict(elements: list, n_swaps: int, seed):
    elements = elements.copy()
    rng = default_rng(seed)
    firsts = rng.choice(elements, size=n_swaps, replace=False)
    # remove them from the list
    for el in firsts:
        elements.remove(el)
    seconds = rng.choice(elements, size=n_swaps, replace=False)
    swap_dict = dict()
    for first, second in zip(firsts, seconds):
        swap_dict[first] = second
        swap_dict[second] = first
    return swap_dict


class Rotor:
    def __init__(self, n_positions: int = 26, seed: int = 0):
        """
        One single rotation permutor in the enigma machine
        :param n_positions: how many positions there are
        :param seed:
        """
        self.seed = seed
        self.n_positions = n_positions

        self.position = 0

        perm_forward, perm_backward = gen_permutor_lists(self.n_positions, self.seed)
        self.perm_forward = perm_forward
        self.perm_backward = perm_backward

    def rotate_return_carryover(self, n_steps: int) -> int:
        div, mod = np.divmod(self.position + n_steps)
        self.position = mod
        return int(div)

    def set_position(self, pos):
        self.position = pos

    def get_permuted_output_forward(self, input_: int):
        idx = np.mod(input_ + self.position, self.n_positions)
        return self.perm_forward[idx]

    def get_permuted_output_backward(self, input_: int):
        idx = np.mod(input_ + self.position, self.n_positions)
        return self.perm_backward[idx]


class Reflector:
    def __init__(self, n_positions: int):
        self.n_positions = n_positions

    def get_reflected_output(self, input_: int):
        return input_


class PlugBoard:
    def __init__(self, n_characters: int = 26, n_swaps: int = 10, seed: int = 0):
        assert n_swaps <= n_characters // 2
        self.n_characters = n_characters
        self.n_swaps = n_swaps
        self.seed = seed

        self.swap_dict = gen_swap_dict(list(range(n_characters)), self.n_swaps, self.seed)

    def get_output(self, input_: int):
        return self.swap_dict[input_]


class Enigma:
    def __init__(self, rotors, plugboard: PlugBoard, reflector: Reflector, charset: str = string.ascii_uppercase):
        self.charset = charset
        n_chars = len(charset)

        self.char_to_number_map = dict()
        for i, char in enumerate(self.charset):
            self.char_to_number_map[char] = i

        rotor_lengths = np.array([rot.n_positions for rot in rotors])
        if not np.all(rotor_lengths == n_chars):
            raise ValueError('rotors do not have same number of positions as the chosen character set')
        self.rotors = rotors

        if not plugboard.n_characters == n_chars:
            raise ValueError('plug board does not have the same number of positions as the character set')
        self.plug_board = plugboard

        if not reflector.n_positions == n_chars:
            raise ValueError('reflector does not have the same number of positions as the character set')
        self.reflector = reflector

    def set_rotor_positions(self, positions):
        for rot, pos in zip(self.rotors, positions):
            assert pos < rot.n_positions
            rot.position = pos

    def encode_message(self, input_: str):
        input_ints = [self.char_to_number_map[char] for char in input_]

        output = str()
        for input_int in input_ints:
            number = self.plug_board.get_output(input_int)
            # first rotor always gets rotated with each new character
            rot_step = 1
            for rot in self.rotors:
                rot_step = rot.rotate_return_carryover(rot_step)
                number = rot.get_permuted_output_forward(number)
            number = self.reflector.get_reflected_output(number)
            for rot in reversed(self.rotors):
                number = rot.get_permuted_output_bactward(number)
            number = self.plug_board.get_output(number)

            output += self.charset[number]
