# Import csv to postgresql db

import psycopg2
import pandas as pd

conn = psycopg2.connect("host=localhost dbname=balderdash3 user=postgres password=postgres")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS questions;")

cur.execute('''CREATE TABLE questions (
	qid SERIAL PRIMARY KEY,
	word TEXT NOT NULL,
    phrase TEXT NOT NULL);''')

conn.commit()

df_users = pd.read_csv('./questions.csv', index_col=0)
for idx, u in df_users.iterrows():

    # Data cleaning
    #print(u)
    q = cur.execute(
        '''INSERT INTO questions (word, phrase) VALUES (%s, %s)''', (u.word, u.phrase)
    )
    conn.commit()

cur.close()
conn.close()