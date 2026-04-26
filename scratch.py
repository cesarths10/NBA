import sqlite3
import pandas as pd

conn = sqlite3.connect('gamelogs.db')
df = pd.read_sql_query('SELECT * FROM gamelogs', conn)
df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

def label_for_date(d):
    if pd.isna(d):
        return None
    season_end = d.year + 1 if d.month >= 8 else d.year
    return f"{season_end-1}-{str(season_end)[-2:]}"

df['season_label'] = df['Date'].apply(label_for_date)
df_filtered = df[(df['season_label'] == '2025-26')].copy()
temp_filtered = df_filtered[['Player', 'Date', 'PTS']].copy()
temp_filtered['Date'] = pd.to_datetime(temp_filtered['Date'], errors='coerce')
temp_filtered = temp_filtered.sort_values(['Player', 'Date'], ascending=[True, False])
temp_filtered = temp_filtered.groupby('Player').head(10)
hit_mask = temp_filtered['PTS'].astype(float) >= 50
temp_filtered['Hit'] = hit_mask.astype(int)
agg_df = temp_filtered.groupby('Player').agg(Hits=('Hit', 'sum')).reset_index()
agg_df = agg_df[agg_df['Hits'] > 0]
print("Results for PTS >= 50, n_games=10:")
print(agg_df)
