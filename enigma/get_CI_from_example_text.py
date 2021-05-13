import os
import collections
import math
import dill

# TODO implement more observables such as the trigraphs (what we do is a bi-graph
# can also be sored in a non-nested dict as 'aa', 'ab' etc -> halves the access

def fill_dict_from_str(di, st: str):
    curr_char = st[0]
    for i in range(len(st) - 1):
        next_char = st[i + 1]
        di[curr_char][next_char] += 1
        curr_char = next_char


source_dir = './sample_texts'


files = [os.path.join(source_dir, f) for f in os.listdir(source_dir) if
         os.path.isfile(os.path.join(source_dir, f)) and f.endswith('.txt')]

next_counts = collections.defaultdict(lambda: collections.defaultdict(int))


for f in files:
    with open(f, 'r') as file_:
        text = file_.read()
        text = text.lower()
        text = ''.join(c for c in text if c.isalnum())
        fill_dict_from_str(next_counts, text)
    file_.close()

log_likelihood = collections.defaultdict(lambda: collections.defaultdict(lambda: -10.))

for l in next_counts:
    total_nexts = sum(next_counts[l].values())
    for l2 in next_counts[l]:
        log_likelihood[l][l2] = math.log10(next_counts[l][l2]/total_nexts)

with open('log_likelihoods.dill', 'wb') as out_file:
    dill.dump(log_likelihood, out_file)
out_file.close()
