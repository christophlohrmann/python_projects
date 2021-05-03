import pandas as pd
import numpy as np
import datetime

ALLOWED_GOALS = ['weight', 'reps', 'time']


class Gain():
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
