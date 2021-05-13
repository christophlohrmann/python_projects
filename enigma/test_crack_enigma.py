import string
import enigma
import dill
import unittest as ut

import crack_enigma


class CrackEnigmaTest(ut.TestCase):
    def setup_enigma_and_msg(self, len_msg, n_plugs):
        self.charset = string.ascii_lowercase
        self.n_chars = len(self.charset)

        self.plugboard = enigma.Swapper(n_positions=self.n_chars, n_swaps=n_plugs, seed=41)
        rotor_seeds = [21, 32, 34]
        self.rotors = [enigma.Rotor(n_positions=self.n_chars, seed=seed) for seed in rotor_seeds]
        self.reflector = enigma.Swapper(n_positions=self.n_chars, n_swaps=self.n_chars // 2, seed=3)

        encoder = enigma.Enigma(self.rotors, self.plugboard, self.reflector, charset=self.charset)
        self.rotor_positions = [3, 4, 7]
        encoder.set_rotor_positions(self.rotor_positions)

        message = "The Enigma machine is a cipher device developed and used in the early- to mid-20th century to protect commercial, diplomatic, and military communication. It was employed extensively by Nazi Germany during World War II, in all branches of the German military. The Germans believed, erroneously, that use of the Enigma machine enabled them to communicate securely and thus enjoy a huge advantage in World War II. The Enigma machine was considered to be so secure that even the most top-secret messages were enciphered on its electrical circuits. Enigma has an electromechanical rotor mechanism that scrambles the 26 letters of the alphabet. In typical use, one person enters text on the Enigma's keyboard and another person writes down which of 26 lights above the keyboard lights up at each key press. If plain text is entered, the lit-up letters are the encoded ciphertext. Entering ciphertext transforms it back into readable plaintext. The rotor mechanism changes the electrical connections between the keys and the lights with each keypress. The security of the system depends on a set of machine settings that were generally changed daily during the war, based on secret key lists distributed in advance, and on other settings that were changed for each message. The receiving station has to know and use the exact settings employed by the transmitting station to successfully decrypt a message."
        message = message.lower()
        message = ''.join(c for c in message if c.islower())
        self.message = message[:len_msg]

        self.encrypted_message = encoder.encode_message(self.message)

    def test_crack_with_pairlikelihood(self):
        n_plugs = 2
        self.setup_enigma_and_msg(100, n_plugs)

        with open('./log_likelihoods.dill', 'rb') as read_file:
            lld = dill.load(read_file)
        scorer = crack_enigma.PairLikelihoodScorer(lld)

        decrypted_msg, decoded_pos, decoder_plugboard = crack_enigma.decode_message(self.encrypted_message,
                                                                                    self.rotors,
                                                                                    n_plugs,
                                                                                    self.reflector,
                                                                                    scorer,
                                                                                    charset=self.charset)

        self.assertListEqual(self.rotor_positions, decoded_pos)
        self.assertDictEqual(self.plugboard.swap_dict, decoder_plugboard.swap_dict)

        self.assertEqual(self.message, decrypted_msg)

if __name__ == '__main__':
    ut.main()
