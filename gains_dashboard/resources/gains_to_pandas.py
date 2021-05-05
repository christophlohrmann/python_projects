import pandas as pd
import datetime
import gain

"""
read the ods of the gains and convert it into the format used in the app
"""

df_gains = pd.read_excel('./the_gains.ods', engine='odf', header=[0, 1])
dates = df_gains['Date']



gains_df = pd.DataFrame()


series_per_type = dict()

# Go through the list and find all entries, extract new_gain data
for type, subtype in df_gains.columns.values:
    with_date = dates.copy().join(df_gains[(type, subtype)])
    valid_entries = with_date.dropna()

    if type == 'Date':
        continue

    if not type in series_per_type:
        series_per_type[type] = dict()

    for idx, entry in valid_entries.iterrows():
        date_time = pd.to_datetime(entry["Date"], format="%d.%m.%Y")
        date = datetime.date(date_time.year, date_time.month, date_time.day)
        value = entry[(type, subtype)]

        new_gain = gain.Gain(type, date)
        # now sort it in correctly
        if isinstance(subtype, int):
            maybe_new_series = gain.WeightSeries(type, reps=subtype)
            new_gain.weight = value

            new_gain.goal = maybe_new_series.goal
            new_gain.reps = maybe_new_series.reps
            new_gain.subtype = maybe_new_series.name

        elif isinstance(subtype, str):
            if subtype.startswith('Reps with'):
                maybe_new_series = gain.RepSeries(type, weight=float(subtype.lstrip('Reps with ')))
                new_gain.reps = value

                new_gain.goal = maybe_new_series.goal
                new_gain.weight = maybe_new_series.weight
                new_gain.time = maybe_new_series.time
                new_gain.subtype = maybe_new_series.name

            elif subtype.startswith('Reps in'):
                maybe_new_series = gain.RepSeries(type, time = float(subtype.lstrip('Reps in ')))
                new_gain.goal = maybe_new_series.goal
                new_gain.reps = value
                new_gain.weight = maybe_new_series.weight
                new_gain.time = maybe_new_series.time
                new_gain.subtype = maybe_new_series.name

            elif subtype.startswith('Time for '):
                maybe_new_series = gain.TimeSeries(type, reps = int(subtype.lstrip('Time for ')))
                new_gain.goal = maybe_new_series.goal
                new_gain.time = value
                new_gain.reps = maybe_new_series.reps
                new_gain.weight = maybe_new_series.weight
                new_gain.subtype = maybe_new_series.name

            elif subtype.startswith('Time with '):
                maybe_new_series = gain.TimeSeries(type, reps=1, weight=float(subtype.lstrip('Time with ')))
                new_gain.goal = maybe_new_series.goal
                new_gain.time = value
                new_gain.weight = maybe_new_series.weight
                new_gain.subtype = maybe_new_series.name
            else:
                ValueError('Subtype unknown')
        else:
            raise ValueError('Subtype unknown')

        if not maybe_new_series.name in series_per_type[type].keys():
            series_per_type[type][maybe_new_series.name] = maybe_new_series

        gains_df = gains_df.append(new_gain.to_data_frame(), ignore_index=True)

series_df = pd.DataFrame()
for type in series_per_type.keys():
    for name in series_per_type[type]:
        series = series_per_type[type][name]
        series_df = series_df.append(series.to_data_frame(), ignore_index=True)


gains_df.sort_values(by='date', inplace=True)
gains_df.to_pickle('the_gains.pick')

series_df.to_pickle('series.pick')
