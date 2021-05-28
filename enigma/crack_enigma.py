import collections
import math

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


class GroupLikelihoodScorer(TextScorerBase):
    def __init__(self, loglikelihooddict: dict, not_known_penalty_factor=2):
        """
        :param loglikelihooddict:
        :param not_known_penalty_factor: If a group is encountered that is not in the loglikelihooddict,
        choose a penalty based on the least liely group and the additional penalty factor
        """
        least_likely = min(loglikelihooddict, key=lambda k: loglikelihooddict[k])
        self.lld = collections.defaultdict(lambda: loglikelihooddict[least_likely] * not_known_penalty_factor,
                                           loglikelihooddict)
        self.n_chars_group = len(least_likely)

    def score_text(self, text: str) -> float:
        score = 0.
        n_groups = len(text) - self.n_chars_group + 1
        for i in range(n_groups):
            group = text[i:i + self.n_chars_group]
            score += self.lld[group]
        score /= n_groups
        return score


def decode_message_successive_best(encrypted_message, rotors: list, n_plugs, reflector: enigma.Swapper,
                                   scorer: TextScorerBase,
                                   charset=string.ascii_lowercase, disable_tqdm=False):
    n_chars = rotors[0].n_positions
    # test encoder knows the machine
    decoder_plugboard = enigma.Swapper(n_positions=n_chars)
    decoder_enigma = enigma.Enigma(copy.deepcopy(rotors),
                                   decoder_plugboard,
                                   copy.deepcopy(reflector),
                                   charset=charset)

    # go through all positions and get the score of the output text
    highscore = -np.inf
    best_pos = decoder_enigma.get_rotor_positions()

    # TODO Parallel?
    positions = iter(MultiindexIiterator(len(rotors), n_chars))
    for pos in tqdm.tqdm(positions, disable=disable_tqdm):
        decoder_enigma.set_rotor_positions(pos)
        decoder_try = decoder_enigma.encode_message(encrypted_message)
        score = scorer.score_text(decoder_try)
        if score > highscore:
            highscore = score
            best_pos = pos

    # decode the plugboard
    # we have 10 plugs to distribute
    available_plug_positions = list(range(n_chars))
    for i in tqdm.tqdm(range(n_plugs), disable=disable_tqdm):
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

    return decoded_msg, best_pos, decoder_plugboard


def decode_message_MC(encrypted_message, rotors: list, n_plugs, reflector: enigma.Swapper,
                      scorer: TextScorerBase, score_scale: float = 1,
                      charset=string.ascii_lowercase):
    n_chars = rotors[0].n_positions
    # test encoder knows the machine
    decoder_plugboard = enigma.Swapper(n_positions=n_chars)
    decoder_plugboard.assign_random_swaps(len(charset), n_plugs)
    decoder_enigma = enigma.Enigma(copy.deepcopy(rotors),
                                   decoder_plugboard,
                                   copy.deepcopy(reflector),
                                   charset=charset)

    last_rotor_positions = decoder_enigma.get_rotor_positions()
    last_dec_msg = decoder_enigma.encode_message(encrypted_message)
    last_score = scorer.score_text(last_dec_msg)

    rng = np.random.default_rng(42)

    def _propose_rot_move(current_rotor_poss: list, rng: np.random.default_rng):
        prop_rotor_pos = current_rotor_poss.copy()
        # pick random rotor
        rot_idx = rng.integers(low=0, high=len(current_rotor_poss), size=1)
        # randomly rotate in one direction
        prop_rotor_pos[rot_idx] += int(round(rng.random() - 0.5))
        return prop_rotor_pos

    def _propose_plug_move(plugboard: enigma.Swapper, rng: np.random.default_rng):
        plug_ends = plugboard.get_swapped_positions()
        free_positions = plugboard.get_free_positions()
        # choose random plug end to connect to a random free location
        return rng.choice(plug_ends), rng.choice(free_positions)

    def _assess_move(decoder_enigma: enigma.Enigma, scorer:TextScorerBase, old_score:float, score_scale:float, rng:np.random.default_rng):
        # get the new score
        rotor_pos = decoder_enigma.get_rotor_positions()
        decoder_try = decoder_enigma.encode_message(encrypted_message)
        decoder_enigma.set_rotor_positions(rotor_pos)
        new_score = scorer.score_text(decoder_try)

        # mc decision making
        r = rng.random()
        return r < math.exp((new_score-old_score) / score_scale), new_score

    for _ in range(10000):
        # rotor move
        prop_rot_pos = _propose_rot_move(last_rotor_positions, rng)
        decoder_enigma.set_rotor_positions(prop_rot_pos)
        accept, new_score = _assess_move(decoder_enigma, scorer, last_score, score_scale, rng)
        if accept:
            last_score = new_score
            last_rotor_positions = prop_rot_pos

        # plugboard move
        prop_plug_move = _propose_plug_move(decoder_plugboard, rng)
        decoder_plugboard.move_one_swap_side(prop_plug_move[0], prop_plug_move[1])
        accept, new_score = _assess_move(decoder_enigma, scorer, last_score, score_scale, rng)
        if accept:
            last_score = new_score
        else:
            # undo the move
            decoder_plugboard.move_one_swap_side(prop_plug_move[1], prop_plug_move[0])

    # use the final settings to return
    decoded_msg = decoder_enigma.encode_message(encrypted_message)

    return decoded_msg, last_rotor_positions, decoder_plugboard




