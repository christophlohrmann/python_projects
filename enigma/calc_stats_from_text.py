import os
import collections
import math
import dill
import string
import tqdm

# TODO implement more observables such as the trigraphs (what we do is a bi-graph
# can also be sored in a non-nested dict as 'aa', 'ab' etc -> halves the access

source_dir = './sample_texts'

files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if
         os.path.isfile(os.path.join(source_dir, f)) and f.endswith('.txt')]

diads = collections.defaultdict(float)
triads = collections.defaultdict(float)
quads = collections.defaultdict(float)

charset = string.ascii_lowercase

n_chars = 0
for f in files:
    with open(f, 'r') as file_:
        print(f'reading {f}')
        text = file_.read()
        print(f'preparing {f}')
        text = text.lower()
        text = ''.join(c for c in text if c in charset)
        print(f'processing {f}')
        for i in tqdm.tqdm(range(len(text) - 4)):
            quad = text[i:i + 4]
            quads[quad] += 1
            triads[quad[:3]] += 1
            diads[quad[:2]] += 1
            n_chars += 1

    file_.close()

for di in [diads, triads, quads]:
    for key in di.keys():
        di[key] = math.log10(di[key] / n_chars)

# return the defaultdict into a dict
# (the user can turn it back into a defaultdict and choose the default value after loading this stats data


res = {'charset': charset,
       'diads': dict(diads),
       'triads': dict(triads),
       'quads': dict(quads)}

with open('language_stats.dill', 'wb') as out_file:
    dill.dump(res, out_file)
out_file.close()
