import pandas as pd
import os

try:
    df = pd.read_csv('UFC dataset/Medium set/medium_dataset.csv')
    print(df['status'].unique())
except Exception as e:
    print(e)
