import time
import string
import random
import tqdm

import enigma

n_messages = 3000
chars_per_message = 256
charset = string.ascii_uppercase
n_chars = len(charset)

plugboard = enigma.Swapper(n_positions=n_chars, n_swaps=10, seed=41)
rotor_seeds = [21, 32, 34]
rotors = [enigma.Rotor(n_positions=n_chars, seed=seed) for seed in rotor_seeds]
reflector = enigma.Swapper(n_positions=n_chars, n_swaps=n_chars // 2, seed=3)

encoder = enigma.Enigma(rotors, plugboard, reflector, charset=charset)
rotor_positions = [3, 4, 7]

messages = [''.join(random.choices(charset, k=chars_per_message)) for _ in range(n_messages)]
tick = time.time()
for message in tqdm.tqdm(messages):
    encoder.set_rotor_positions(rotor_positions)
    encoded_message = encoder.encode_message(message)
tock = time.time()

avg_time = (tock-tick)/n_messages

print(f'Average encoding time for message with {chars_per_message} characters: {avg_time:.2e} seconds')



