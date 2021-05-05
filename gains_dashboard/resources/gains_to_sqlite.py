import sqlite3
import pandas as pd

df_gains = pd.read_pickle('./the_gains.pick')
df_series = pd.read_pickle('./series.pick')

conn = sqlite3.connect('the_gains.db')
df_gains.to_sql('the_gains', conn, if_exists ='replace', index = False)
df_series.to_sql('series', conn, if_exists ='replace', index = False)
