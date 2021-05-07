import unittest as ut
import enigma
import string


class SwapperTest(ut.TestCase):
    def test_plugboard(self):
        plugboard = enigma.Swapper(n_positions=10, n_swaps=5, seed=42)
        in_0 = 3
        out_0 = plugboard.get_output(in_0)
        self.assertNotEqual(in_0, out_0)
        self.assertEqual(in_0, plugboard.get_output(out_0))

        plugboard_noswap = enigma.Swapper(n_positions=10, n_swaps=0, seed=42)
        in_1 = 5
        out_1 = plugboard_noswap.get_output(in_1)
        self.assertEqual(in_1, out_1)


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
    test_message = 'thisisaverymeaninglesstestmessagebutititsmorethentwentysixcharacterslong'

    def test_encrypt_decrypt(self):
        plugboard = enigma.Swapper(n_positions=self.n_chars, n_swaps=10, seed=41)
        rotor = enigma.Rotor(n_positions=self.n_chars, seed=4)
        reflector = enigma.Swapper(n_positions=self.n_chars, n_swaps=self.n_chars//2, seed=3)

        encoder = enigma.Enigma([rotor], plugboard, reflector, charset=self.charset)
        encoder.set_rotor_positions([3])

        encoded_message = encoder.encode_message(self.test_message)
        self.assertNotEqual(encoded_message, self.test_message)

        encoder.set_rotor_positions([3])
        decoded_message = encoder.encode_message(encoded_message)
        self.assertEqual(decoded_message, self.test_message)



if __name__ == '__main__':
    ut.main()
