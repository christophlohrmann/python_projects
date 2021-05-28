import numpy as np

import string


def gen_permutor_lists(n_elements: int, seed: int):
    elements = range(n_elements)
    rng = np.random.default_rng(seed)
    perm_forward = rng.permutation(elements).tolist()
    perm_backward = [perm_forward.index(el) for el in elements]

    return perm_forward, perm_backward


def gen_swap_dict(elements: list, n_swaps: int, seed):
    elements = elements.copy()
    rng = np.random.default_rng(seed)

    # random input jacks of the board
    firsts = rng.choice(elements, size=n_swaps, replace=False)
    # remove them from the list
    for el in firsts:
        elements.remove(el)

    # random output jacks
    seconds = rng.choice(elements, size=n_swaps, replace=False)
    # again remove from the list
    for el in seconds:
        elements.remove(el)

    # and the ports that are not connected
    leftover = elements

    swap_dict = dict()
    for first, second in zip(firsts, seconds):
        swap_dict[first] = second
        swap_dict[second] = first
    for el in leftover:
        swap_dict[el] = el
    return swap_dict


class Rotor:
    def __init__(self, n_positions: int = 26, seed: int = 0):
        self.seed = seed
        self.n_positions = n_positions

        self.position = 0

        # who is connected to who at pos 0:
        positions = np.arange(self.n_positions)
        rng = np.random.default_rng(seed)
        connected_forward = rng.permutation(positions)
        connected_backwards = np.array([np.where(connected_forward == pos) for pos in positions]).squeeze()

        # the actual wiring, i.e. the relative difference between the connections on the in-side and the out-side
        self.forward_adds = connected_forward - positions
        self.backward_adds = connected_backwards - positions

    def rotate_return_carryover(self, n_steps: int) -> int:
        div, mod = np.divmod(self.position + n_steps, self.n_positions)
        self.position = mod
        return int(div)

    def set_position(self, pos: int):
        self.position = pos % self.n_positions

    def get_permuted_output_forward(self, input_: int) -> int:
        add_idx = (input_ + self.position) % self.n_positions
        return int((input_ + self.forward_adds[add_idx]) % self.n_positions)

    def get_permuted_output_backward(self, input_: int) -> int:
        add_idx = (input_ + self.position) % self.n_positions
        return int((input_ + self.backward_adds[add_idx]) % self.n_positions)


class Swapper:
    def __init__(self, n_positions: int = 26):
        self.n_positions = n_positions
        self.swap_dict = gen_swap_dict(list(range(self.n_positions)), 0, 0)

    def set_element_swap(self, e1: int, e2: int):
        self.swap_dict[e1] = e2
        self.swap_dict[e2] = e1

    def unset_element_swap(self, e1: int, e2: int):
        self.swap_dict[e1] = e1
        self.swap_dict[e2] = e2

    def get_output(self, input_: int) -> int:
        return self.swap_dict[input_]

    def assign_random_swaps(self, n_swaps: int, seed: int):
        assert n_swaps <= self.n_positions // 2
        self.swap_dict = gen_swap_dict(list(range(self.n_positions)), n_swaps, seed)


class Enigma:
    def __init__(self, rotors, plugboard: Swapper, reflector: Swapper, charset: str = string.ascii_uppercase):
        self.charset = charset
        n_chars = len(charset)

        self.char_to_number_map = dict()
        for i, char in enumerate(self.charset):
            self.char_to_number_map[char] = i

        rotor_lengths = np.array([rot.n_positions for rot in rotors])
        if not np.all(rotor_lengths == n_chars):
            raise ValueError('rotors do not have same number of positions as the chosen character set')
        self.rotors = rotors

        if not plugboard.n_positions == n_chars:
            raise ValueError('plug board does not have the same number of positions as the character set')
        self.plug_board = plugboard

        if not reflector.n_positions == n_chars:
            raise ValueError('reflector does not have the same number of positions as the character set')
        self.reflector = reflector

    def set_rotor_positions(self, positions):
        for rot, pos in zip(self.rotors, positions):
            assert pos < rot.n_positions
            rot.position = pos

    def get_rotor_positions(self):
        return [rot.position for rot in self.rotors]

    def encode_message(self, input_: str) -> str:
        input_ints = [self.char_to_number_map[char] for char in input_]

        output = str()
        for input_int in input_ints:
            number = self.plug_board.get_output(input_int)
            # first rotor always gets rotated with each new character
            rot_step = 1
            for rot in self.rotors:
                rot_step = rot.rotate_return_carryover(rot_step)
                number = rot.get_permuted_output_forward(number)
            number = self.reflector.get_output(number)
            for rot in reversed(self.rotors):
                number = rot.get_permuted_output_backward(number)
            number = self.plug_board.get_output(number)

            output += self.charset[number]

        return output
