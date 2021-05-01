import pandas as pd
import numpy as np

df = pd.read_excel('./the_gains.ods', engine='odf', header=[0, 1])

class Gain():
    def __init__(self, type_, date, subtype = 'misc', goal = 'weight', weight = 0., reps = 1, time = np.nan):
        self.type = type_
        self.subtype = subtype
        self.date = date
        self.goal = goal
        self.weight = weight
        self.reps = reps
        self.time = time

    def to_data_frame(self):
        # make all args to lists

        d = self.__dict__.copy()
        for key in d.keys():
            d[key] = [d[key]]

        return pd.DataFrame(data = d)

dates  = df['Date']

test_gain = Gain('test','20.07.1988')
print(test_gain.to_data_frame())

gains_df = pd.DataFrame(columns=test_gain.__dict__.keys())


# Go through the list and find all entries, extract gain data
for type, subtype in df.columns.values:
    with_date = dates.copy().join(df[(type, subtype)])
    valid_entries = with_date.dropna()

    if type == 'Date':
        continue

    for idx, entry in valid_entries.iterrows():
        date = pd.to_datetime(entry["Date"], format = "%d.%m.%Y")
        value = entry[(type, subtype)]

        gain = Gain(type, date, subtype=subtype)
        # now sort it in correctly
        if isinstance(subtype, int):
            gain.goal = 'weight'
            gain.weight = value
            gain.reps = subtype
            gain.subtype = f'{subtype} rep max'
        elif isinstance(subtype, str):
            if subtype.startswith('Reps with'):
                gain.goal = 'reps'
                gain.reps = value
                gain.weight = float(subtype.lstrip('Reps with '))
            elif subtype.startswith('Reps in'):
                gain.goal = 'reps'
                gain.reps = value
                gain.weight = 0
                gain.time = float(subtype.lstrip('Reps in '))
            elif subtype.startswith('Time for '):
                gain.goal = 'time'
                gain.time = value
                gain.reps = int(subtype.lstrip('Time for '))
            elif subtype.startswith('Time with '):
                gain.goal = 'time'
                gain.time = value
                gain.weight = float(subtype.lstrip('Time with '))
            else:
                ValueError('Subtype unknown')
        else:
            raise ValueError('Subtype unknown')

        gains_df = gains_df.append(gain.to_data_frame(), ignore_index=True)

gains_df.sort_values(by = 'date', inplace=True)

gains_df.to_pickle('the_gains.pick')





