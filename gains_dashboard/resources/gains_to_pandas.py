import pandas as pd
import datetime
import gain

df = pd.read_excel('./the_gains.ods', engine='odf', header=[0, 1])
dates = df['Date']

gains_df = pd.DataFrame()
# Go through the list and find all entries, extract new_gain data
for type, subtype in df.columns.values:
    with_date = dates.copy().join(df[(type, subtype)])
    valid_entries = with_date.dropna()

    if type == 'Date':
        continue

    for idx, entry in valid_entries.iterrows():
        date_time = pd.to_datetime(entry["Date"], format="%d.%m.%Y")
        date = datetime.date(date_time.year, date_time.month, date_time.day)
        value = entry[(type, subtype)]

        new_gain = gain.Gain(type, date, subtype=subtype)
        # now sort it in correctly
        if isinstance(subtype, int):
            new_gain.goal = 'weight'
            new_gain.weight = value
            new_gain.reps = subtype
            new_gain.subtype = f'{subtype} rep max'
        elif isinstance(subtype, str):
            if subtype.startswith('Reps with'):
                new_gain.goal = 'reps'
                new_gain.reps = value
                new_gain.weight = float(subtype.lstrip('Reps with '))
            elif subtype.startswith('Reps in'):
                new_gain.goal = 'reps'
                new_gain.reps = value
                new_gain.weight = 0
                new_gain.time = float(subtype.lstrip('Reps in '))
            elif subtype.startswith('Time for '):
                new_gain.goal = 'time'
                new_gain.time = value
                new_gain.reps = int(subtype.lstrip('Time for '))
            elif subtype.startswith('Time with '):
                new_gain.goal = 'time'
                new_gain.time = value
                new_gain.weight = float(subtype.lstrip('Time with '))
            else:
                ValueError('Subtype unknown')
        else:
            raise ValueError('Subtype unknown')

        gains_df = gains_df.append(new_gain.to_data_frame(), ignore_index=True)

gains_df.sort_values(by='date', inplace=True)

gains_df.to_pickle('the_gains.pick')
