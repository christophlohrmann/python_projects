import dill
import string

import unittest as ut

import enigma
import crack_enigma


def string_compare(s1: string, s2: string) -> float:
    n_same = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            n_same += 1
    return n_same / len(s1)


class UtilsTest(ut.TestCase):
    def test_multiindexiterator(self):
        it = iter(crack_enigma.MultiindexIiterator(2, 3))
        shouldbe = [
            [0, 0],
            [0, 1],
            [0, 2],
            [1, 0],
            [1, 1],
            [1, 2],
            [2, 0],
            [2, 1],
            [2, 2],
        ]
        for i, s in zip(it, shouldbe):
            self.assertListEqual(i, s)

    def test_string_compare(self):
        a = "abcdff"
        b = "abefff"
        self.assertAlmostEqual(string_compare(a, b), 2.0 / 3.0)


class SwapperTest(ut.TestCase):
    def test_plugboard_random_swaps(self):
        plugboard = enigma.Swapper(n_positions=10)
        in_1 = 5
        out_1 = plugboard.get_output(in_1)
        self.assertEqual(in_1, out_1)

        plugboard.assign_random_swaps(n_swaps=5, seed=42)
        in_0 = 3
        out_0 = plugboard.get_output(in_0)
        self.assertNotEqual(in_0, out_0)
        self.assertEqual(in_0, plugboard.get_output(out_0))

    def test_swap_methods(self):
        plugboard = enigma.Swapper(n_positions=10)

        # element swap
        plugboard.set_element_swap(3, 7)
        self.assertEqual(plugboard.get_output(3), 7)
        self.assertEqual(plugboard.get_output(7), 3)
        self.assertEqual(plugboard.get_output(2), 2)

        # swap move
        plugboard.move_one_swap_side(7, 8)
        self.assertEqual(plugboard.get_output(3), 8)
        self.assertEqual(plugboard.get_output(8), 3)
        self.assertEqual(plugboard.get_output(7), 7)
        self.assertEqual(plugboard.get_output(2), 2)

        with self.assertRaises(ValueError):
            plugboard.move_one_swap_side(2, 3)

        plugboard.set_element_swap(2, 1)
        with self.assertRaises(ValueError):
            plugboard.move_one_swap_side(8, 2)

        # swap remove
        plugboard.unset_element_swap(3, 8)
        self.assertEqual(plugboard.get_output(7), 7)
        self.assertEqual(plugboard.get_output(8), 8)


class RotorTest(ut.TestCase):
    def test_rotor(self):
        rotor = enigma.Rotor(n_positions=10, seed=42)

        rotor.set_position(9)
        carryover = rotor.rotate_return_carryover(1)
        self.assertEqual(rotor.position, 0)
        self.assertEqual(carryover, 1)

        rotor.position = 6
        in_ = 7
        out = rotor.get_permuted_output_forward(in_)
        self.assertEqual(rotor.get_permuted_output_backward(out), in_)

        rotor.rotate_return_carryover(1)
        out2 = rotor.get_permuted_output_forward(in_)
        self.assertNotEqual(out, out2)


class EnigmaTest(ut.TestCase):
    charset = string.ascii_lowercase
    n_chars = len(charset)
    test_message = (
        "thisisaverymeaninglesstestmessagebutititsmorethentwentysixcharacterslong"
    )

    def test_encrypt_decrypt(self):
        plugboard = enigma.Swapper(n_positions=self.n_chars)
        plugboard.assign_random_swaps(n_swaps=10, seed=41)
        rotor_seeds = [21, 32, 34]
        rotors = [
            enigma.Rotor(n_positions=self.n_chars, seed=seed) for seed in rotor_seeds
        ]
        reflector = enigma.Swapper(n_positions=self.n_chars)
        reflector.assign_random_swaps(n_swaps=self.n_chars // 2, seed=3)

        encoder = enigma.Enigma(rotors, plugboard, reflector, charset=self.charset)
        rotor_positions = [3, 4, 7]

        encoder.set_rotor_positions(rotor_positions)
        encoded_message = encoder.encode_message(self.test_message)
        self.assertNotEqual(encoded_message, self.test_message)

        encoder.set_rotor_positions(rotor_positions)
        decoded_message = encoder.encode_message(encoded_message)
        self.assertEqual(decoded_message, self.test_message)


class CrackEnigmaCommon:
    def setup_enigma_and_msg(self, len_msg, n_rotors, n_plugs):
        self.charset = string.ascii_lowercase
        self.n_chars = len(self.charset)

        self.reflector = enigma.Swapper(n_positions=self.n_chars)
        self.reflector.assign_random_swaps(n_swaps=self.n_chars // 2, seed=3)

        rotor_seeds = list(range(n_rotors))
        self.rotors = [
            enigma.Rotor(n_positions=self.n_chars, seed=seed) for seed in rotor_seeds
        ]
        self.rotor_positions = n_rotors * [15]

        self.plugboard = enigma.Swapper(n_positions=self.n_chars)
        self.plugboard.assign_random_swaps(n_swaps=n_plugs, seed=41)

        message = (
            "The Enigma machine is a cipher device developed and used in the early- to mid-20th century to protect"
            " commercial, diplomatic, and military communication. It was employed extensively by Nazi Germany during "
            "World War II, in all branches of the German military. The Germans believed, erroneously, that use of the"
            " Enigma machine enabled them to communicate securely and thus enjoy a huge advantage in World War II. "
            "The Enigma machine was considered to be so secure that even the most top-secret messages were enciphered"
            " on its electrical circuits. Enigma has an electromechanical rotor mechanism that scrambles the 26 letters "
            "of the alphabet. In typical use, one person enters text on the Enigma's keyboard and another person writes"
            " down which of 26 lights above the keyboard lights up at each key press. If plain text is entered, the "
            "lit-up letters are the encoded ciphertext. Entering ciphertext transforms it back into readable plaintext. "
            "The rotor mechanism changes the electrical connections between the keys and the lights with each keypress. "
            "The security of the system depends on a set of machine settings that were generally changed daily during the "
            "war, based on secret key lists distributed in advance, and on other settings that were changed for "
            "each message. The receiving station has to know and use the exact settings employed by the transmitting "
            "station to successfully decrypt a message."
        )
        message = message.lower()
        self.message_full = "".join(c for c in message if c.islower())

        encoder = enigma.Enigma(
            self.rotors, self.plugboard, self.reflector, charset=self.charset
        )
        encoder.set_rotor_positions(self.rotor_positions)
        self.message = self.message_full[:len_msg]
        self.encrypted_message = encoder.encode_message(self.message)

        # reset all rotors so MC does not start with a good value
        encoder.set_rotor_positions(n_rotors * [0])


class CrackEnigmaSuccessiveBestTest(ut.TestCase, CrackEnigmaCommon):
    def test_diad_cracking(self):
        self.check_crack_with_grouplikelihood("diads")

    def test_triad_cracking(self):
        self.check_crack_with_grouplikelihood("triads")

    def testquad_cracking(self):
        self.check_crack_with_grouplikelihood("quads")

    def check_crack_with_grouplikelihood(self, groupname: str):
        n_plugs = 2
        n_rotors = 2
        self.setup_enigma_and_msg(100, n_rotors, n_plugs)

        with open("./language_stats.dill", "rb") as read_file:
            group_likelihood = dill.load(read_file)[groupname]
        scorer = crack_enigma.GroupLikelihoodScorer(group_likelihood)

        (
            decrypted_msg,
            decoded_pos,
            decoder_plugboard,
        ) = crack_enigma.decode_message_successive_best(
            self.encrypted_message,
            self.rotors,
            n_plugs,
            self.reflector,
            scorer,
            charset=self.charset,
            disable_tqdm=True,
        )

        self.assertListEqual(self.rotor_positions, decoded_pos)
        self.assertDictEqual(self.plugboard.swap_dict, decoder_plugboard.swap_dict)

        self.assertEqual(self.message, decrypted_msg)


class CrackEnigmaMCTest(ut.TestCase, CrackEnigmaCommon):
    def test_triad_cracking(self):
        n_plugs = 0
        n_rotors = 1
        self.setup_enigma_and_msg(200, n_rotors, n_plugs)

        with open("./language_stats.dill", "rb") as read_file:
            group_likelihood = dill.load(read_file)["triads"]
        scorer = crack_enigma.GroupLikelihoodScorer(group_likelihood)

        decrypted_msg, decoded_pos, decoder_plugboard = crack_enigma.decode_message_MC(
            self.encrypted_message,
            self.rotors,
            n_plugs,
            self.reflector,
            scorer,
            charset=self.charset,
            score_scale=0.2,
            n_attempts_per_block=100,
            max_n_blocks=100,
        )
        self.assertGreater(string_compare(decrypted_msg, self.message), 0.85)


if __name__ == "__main__":
    ut.main()
