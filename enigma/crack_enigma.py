import collections
import baseconvert
import string
import numpy as np
import copy
import tqdm

import enigma


class MultiindexIiterator:
    def __init__(self, n_dims, n_val_per_dim):
        self.n_dims = n_dims
        self.n_val_per_dim = n_val_per_dim
        self.lin_idx = 0

        self.len = self.n_val_per_dim ** self.n_dims

    def __len__(self):
        return self.len

    def __iter__(self):
        self.lin_idx = 1
        return self

    def __next__(self):
        if self.lin_idx < self.len:
            baseconverted = list(baseconvert.base(self.lin_idx, 10, self.n_val_per_dim))
            n_pad_zeros = self.n_dims - len(baseconverted)
            self.lin_idx += 1
            return n_pad_zeros * [0] + baseconverted
        else:
            raise StopIteration


class TextScorerBase:
    def score_text(self, text: str) -> float:
        raise NotImplementedError


class PairLikelihoodScorer(TextScorerBase):
    def __init__(self, loglikelihooddict: collections.defaultdict):
        self.lld = loglikelihooddict

    def score_text(self, text: str) -> float:
        score = 0.
        current_char = text[0]
        for i in range(len(text) - 1):
            next_char = text[i + 1]
            score += self.lld[current_char][next_char]
            current_char = next_char
        score /= (len(text) - 1)
        return score


def decode_message(encrypted_message, rotors: list, n_plugs, reflector: enigma.Swapper, scorer: TextScorerBase,
                   charset=string.ascii_lowercase, debug_msg=False):
    n_chars = rotors[0].n_positions
    # test encoder knows the machine
    decoder_plugboard = enigma.Swapper(n_positions=n_chars, n_swaps=0)
    decoder_enigma = enigma.Enigma(copy.deepcopy(rotors),
                                   decoder_plugboard,
                                   copy.deepcopy(reflector),
                                   charset=charset)
    decoder_enigma.set_rotor_positions([0, 0, 0])

    # go through all positions and get the score of the output text
    highscore = -np.inf
    best_pos = 3 * [0]

    # Parallel?
    positions = iter(MultiindexIiterator(len(rotors), n_chars))
    for pos in tqdm.tqdm(positions):
        decoder_enigma.set_rotor_positions(pos)
        decoder_try = decoder_enigma.encode_message(encrypted_message)
        score = scorer.score_text(decoder_try)
        if score > highscore:
            highscore = score
            best_pos = pos

    decoder_enigma.set_rotor_positions(best_pos)
    decoded_msg = decoder_enigma.encode_message(encrypted_message)
    if debug_msg:
        print('After rotor selection: ', decoded_msg)

    # decode the plugboard
    # we have 10 plugs to distribute
    available_plug_positions = list(range(n_chars))
    for i in tqdm.tqdm(range(n_plugs)):
        highscore = -np.inf
        best_swap = (0, 1)
        # go through all positions for the plug and get their score
        # TODO loop parallel?
        for first in available_plug_positions:
            for second in available_plug_positions:
                # we have to set a plug, self-connections are not allowed
                if first == second:
                    continue
                decoder_plugboard.set_element_swap(first, second)
                decoder_enigma.set_rotor_positions(best_pos)
                decoder_try = decoder_enigma.encode_message(encrypted_message)
                score = scorer.score_text(decoder_try)
                if score > highscore:
                    highscore = score
                    best_swap = (first, second)
                decoder_plugboard.unset_element_swap(first, second)

        # use the best swap for further decrypting
        decoder_plugboard.set_element_swap(best_swap[0], best_swap[1])
        available_plug_positions.remove(best_swap[0])
        available_plug_positions.remove(best_swap[1])

    decoder_enigma.set_rotor_positions(best_pos)
    decoded_msg = decoder_enigma.encode_message(encrypted_message)

    if debug_msg:
        print('After plugboard selection :', decoded_msg)

    return decoded_msg, best_pos, decoder_plugboard
