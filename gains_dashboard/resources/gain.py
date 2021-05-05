import pandas as pd
import numpy as np
import datetime

ALLOWED_GOALS = ['weight', 'reps', 'time']


class Gain:
    def __init__(self, type_, date, subtype='misc', goal='weight', weight=0., reps=1, time=np.nan):
        self.type = type_
        self.subtype = subtype
        if not isinstance(date, datetime.date):
            raise TypeError(f'type of date [{type(date)}] must be datetime.date')
        # when converting to sql entry, dates will be converted to strings anyways
        self.date = str(date)
        if goal not in ALLOWED_GOALS:
            raise ValueError(f'goal {goal} is not in {ALLOWED_GOALS}')
        self.goal = goal

        self.weight = weight
        self.reps = reps
        self.time = time

    def to_data_frame(self):
        # make all args to lists

        d = self.__dict__.copy()
        for key in d.keys():
            d[key] = [d[key]]

        return pd.DataFrame(data=d)


class Series:
    def __init__(self, type_):
        self.type = type_

    def gain_belongs_to_series(self, gain):
        raise NotImplementedError

    def to_data_frame(self):
        # make all args to lists

        d = self.__dict__.copy()
        for key in d.keys():
            d[key] = [d[key]]

        return pd.DataFrame(data=d)


class RepSeries(Series):
    def __init__(self, type_, weight=0, time=None):
        super(RepSeries, self).__init__(type_)
        self.goal = 'reps'
        self.weight = weight
        self.name = f'Max reps with {weight} kg'

        if time is None:
            self.time = np.inf
        else:
            self.time = time
            self.name += f' in {self.time} s'

    def gain_belongs_to_series(self, gain):
        return gain.weight == self.weight and gain.time == self.time


class WeightSeries(Series):
    def __init__(self, type_, reps=1, time=None):
        super(WeightSeries, self).__init__(type_)
        self.goal = 'weight'
        self.reps = reps
        self.name = f'{reps} rep max'

        if time is None:
            self.time = np.inf
        else:
            self.time = time
            self.name += f' in {self.time} s'

    def gain_belongs_to_series(self, gain):
        return gain.reps == self.reps and gain.time == self.time


class TimeSeries(Series):
    def __init__(self, type_, reps=1, weight=0):
        super(TimeSeries, self).__init__(type_)
        self.goal = 'time'
        self.reps = reps
        self.weight = weight
        self.name = f'time for {reps} reps with {weight} kg'

    def gain_belongs_to_series(self, gain):
        return gain.weight == self.weight and gain.reps == self.reps
