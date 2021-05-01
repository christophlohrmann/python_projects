import sqlite3
import pandas as pd

df = pd.read_pickle('./the_gains.pick')
conn = sqlite3.connect('the_gains.db')
df.to_sql('the_gains', conn, if_exists = 'replace', index = False)
