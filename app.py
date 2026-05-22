import streamlit as st
import traceback

st.set_page_config(layout="wide", page_title="NBA Player Game Logs")

# Custom Styles for Premium UI
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Global Font Face */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    color: #0f172a;
}

/* Premium Card Panels */
.premium-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(226, 232, 240, 0.8);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    margin-bottom: 1.5rem;
}

/* Styled metric badges */
.metric-badge {
    background-color: rgba(15, 23, 42, 0.05);
    color: #0f172a;
    border: 1px solid rgba(15, 23, 42, 0.1);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 10px;
    display: inline-block;
    text-align: center;
    width: 100%;
}
</style>
""", unsafe_allow_html=True)

try:
    import pandas as pd
    from datetime import datetime
    import os
    import sqlite3
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()
except Exception as e:
    st.error(f"Startup Error: {e}")
    st.text(traceback.format_exc())
    st.stop()


def check_password():
    """Returns `True` if the user had the correct password."""
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs
    with st.form("login_form"):
        st.write("### Login")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    
    if submit:
        if "users" in st.secrets and user in st.secrets["users"] and st.secrets["users"][user] == pwd:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not found or password incorrect")
        
    return False

try:
    if check_password():
        DB_PATH = "gamelogs.db"

        def db_mtime(path):
            return os.path.getmtime(path) if os.path.exists(path) else 0

        @st.cache_data
        def load_gamelogs(db_path, mtime):
            if not os.path.exists(db_path):
                return pd.DataFrame()
            try:
                conn = sqlite3.connect(db_path)
                df = pd.read_sql_query("SELECT * FROM gamelogs", conn)
                conn.close()
                if not df.empty:
                    df['season_label'] = df['Season']
                    df['is_preseason'] = df['GameType'] == 'Preseason'
                return df
            except Exception as e:
                st.error(f"Error reading database: {e}")
                return pd.DataFrame()

        @st.cache_data
        def load_players_data():
            path = "players.xlsx"
            if not os.path.exists(path):
                return pd.DataFrame()
            try:
                return pd.read_excel(path)
            except Exception as e:
                st.error(f"Error reading players.xlsx: {e}")
                return pd.DataFrame()

        df = load_gamelogs(DB_PATH, db_mtime(DB_PATH))
        players_df = load_players_data()

        if df.empty:
            st.warning("No data found in gamelogs.db or database file is missing.")
        else:
            all_players = sorted(df['Player'].unique())

            # Sidebar selectors
            st.sidebar.markdown("## 📊 Navigation & Filters")
            view_mode = st.sidebar.radio('View Mode', ['Select Player', 'Select Stat'])
            
            # Season selector (loaded from pre-calculated database column)
            all_season_labels = sorted(df['season_label'].dropna().unique(), reverse=True)
            selected_seasons = st.sidebar.multiselect('Select Season(s)', all_season_labels, default=all_season_labels[:1] if all_season_labels else [])
            
            # Game Type selector
            all_game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
            selected_game_types = st.sidebar.multiselect('Select Game Type(s)', all_game_types, default=['Regular Season', 'Playoffs'])

            selected_player = None
            if view_mode == 'Select Player':
                selected_player = st.sidebar.selectbox('Select Player', all_players, key='player_select')

            # Filter data based on sidebar settings
            df_filtered = df.copy()
            if selected_seasons:
                df_filtered = df_filtered[df_filtered['season_label'].isin(selected_seasons)]
            if selected_game_types:
                df_filtered = df_filtered[df_filtered['GameType'].isin(selected_game_types)]

            if view_mode == 'Select Player' and selected_player:
                df_filtered = df_filtered[df_filtered['Player'] == selected_player]

            st.title('NBA Player Game Logs')
            
            if view_mode == 'Select Player':
                if selected_player:
                    st.subheader(f"🏀 {selected_player}")
                    st.write("Showing summary stats for Last 5, Last 10, and Last 20 games.")
                else:
                    st.subheader("No player loaded")
                    st.write("Select a player in the sidebar to show detailed summaries.")
            else:
                st.subheader("🏆 Leaderboard View")
                st.write("Showing the Top 10 players who hit the selected stats in their Last 5, 10, and 20 games.")

            columns_to_display = [
                'Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN',
                'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                'P|R|A', 'P|A', 'P|R'
            ]
            stat_fields = ['PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']

            # Target Stat Line Filters Layout
            stat_inputs = {}
            st.markdown('<div class="premium-card">', unsafe_allow_html=True)
            st.markdown("### 🔍 Target Stat Lines")
            
            # Clear filters button
            col_clear, col_spacer = st.columns([1, 4])
            if col_clear.button('Clear Filters', use_container_width=True):
                for stat in stat_fields:
                    st.session_state[f'stat_{stat}'] = None
                st.rerun()

            # Row 1: Primary Metrics
            row1 = st.columns(5)
            primary_stats = ['PTS', 'TPM', 'REB', 'AST', 'STL']
            primary_labels = {
                'PTS': '🏀 Points',
                'TPM': '🎯 3-Pointers',
                'REB': '💪 Rebounds',
                'AST': '🤝 Assists',
                'STL': '⚡ Steals'
            }
            for i, stat in enumerate(primary_stats):
                val = row1[i].number_input(primary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                stat_inputs[stat] = val if val is not None else 0

            # Row 2: Defensive & Combination Metrics
            row2 = st.columns(5)
            secondary_stats = ['BLK', 'TOV']
            secondary_labels = {
                'BLK': '🛡️ Blocks',
                'TOV': '⚠️ Turnovers'
            }
            for i, stat in enumerate(secondary_stats):
                val = row2[i].number_input(secondary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                stat_inputs[stat] = val if val is not None else 0

            combo_stats = [
                ('P|R|A', '🔥 PTS + REB + AST'),
                ('P|A', '🔥 PTS + AST'),
                ('P|R', '🔥 PTS + REB')
            ]
            for i, (stat, label) in enumerate(combo_stats):
                val = row2[i + 2].number_input(label, min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                stat_inputs[stat] = val if val is not None else 0
                
            st.markdown('</div>', unsafe_allow_html=True)

            # Dialog Logic for Popup Game Logs
            try:
                @st.dialog("Player Game Logs")
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.write(f"Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    st.dataframe(df_out, width='stretch', hide_index=True)
            except AttributeError:
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.markdown(f"### Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    st.dataframe(df_out, width='stretch', hide_index=True)

            def make_display_df(df_source, n):
                if df_source.empty:
                    return pd.DataFrame(columns=columns_to_display)
                temp = df_source.sort_values('Date', ascending=False).head(n).copy()
                
                # Calculate combined columns if present
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].astype(float).sum(axis=1)
                
                if 'Date' in temp.columns:
                    temp['Date'] = pd.to_datetime(temp['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                for col in ['FGPercent', 'TPPercent', 'FTPercent', 'FIC']:
                    if col in temp.columns:
                        temp[col] = temp[col].apply(lambda x: f'{x:.3f}' if pd.notnull(x) else '')
                
                for col in columns_to_display:
                    if col not in temp.columns:
                        temp[col] = ''
                        
                return temp[columns_to_display].copy()

            display_5 = make_display_df(df_filtered, 5)
            display_10 = make_display_df(df_filtered, 10)
            display_20 = make_display_df(df_filtered, 20)

            def compute_percent_hits(display_df_local):
                results = {}
                n = len(display_df_local)
                if n == 0:
                    for stat in stat_fields:
                        results[stat] = None
                    return results
                for stat in stat_fields:
                    if stat in display_df_local.columns and stat_inputs[stat] > 0:
                        mask = display_df_local[stat].astype(float) >= stat_inputs[stat]
                        percent = mask.sum() / n * 100
                        results[stat] = percent
                    else:
                        results[stat] = None
                return results

            def render_table_with_summary(display_df_local, title):
                percents = compute_percent_hits(display_df_local)
                
                active_stats = [stat for stat in stat_fields if stat_inputs.get(stat, 0) > 0]
                if active_stats:
                    percent_cols = st.columns(len(active_stats))
                    for i, stat in enumerate(active_stats):
                        percent_str = f"{percents[stat]:.1f}%" if percents[stat] is not None else "-"
                        percent_cols[i].markdown(
                            f'<div class="metric-badge"><b>{stat}:</b> {percent_str}</div>',
                            unsafe_allow_html=True
                        )
                        
                    base_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN']
                    cols_to_keep = [c for c in base_cols + active_stats if c in display_df_local.columns]
                    display_df_local = display_df_local[cols_to_keep]

                try:
                    def highlight_rows(s):
                        highlight = []
                        for idx, row in s.iterrows():
                            row_highlight = True
                            has_filter = False
                            for stat in stat_fields:
                                if stat_inputs[stat] > 0:
                                    has_filter = True
                                    if stat not in row or pd.isnull(row[stat]):
                                        row_highlight = False
                                        break
                                    try:
                                        if float(row[stat]) < stat_inputs[stat]:
                                            row_highlight = False
                                            break
                                    except Exception:
                                        row_highlight = False
                                        break
                            
                            if not has_filter:
                                row_highlight = False
                            
                            # Soft pastel green highlight
                            highlight.append('background-color: rgba(16, 185, 129, 0.12)' if row_highlight else '')
                        return pd.DataFrame([highlight]*len(s.columns)).T
                    
                    styled = display_df_local.style.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+7)', props=[('text-align', 'left')]), # Text columns left-aligned
                        dict(selector='th:nth-child(-n+7)', props=[('text-align', 'left')])
                    ]).apply(lambda _: highlight_rows(display_df_local), axis=None)
                    st.dataframe(styled, width='stretch', hide_index=True)
                except Exception as e:
                    st.dataframe(display_df_local, width='stretch', hide_index=True)

            def render_stat_summary(df_all, players_base_df, n_games, title):
                has_active_filters = any(stat_inputs[s] > 0 for s in stat_fields)
                if not has_active_filters:
                    st.info("Input a stat filter above to see top players.")
                    return
                
                if df_all.empty:
                    st.write("No gamelogs available.")
                    return
                
                temp = df_all.copy()
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].astype(float).sum(axis=1)

                cols_to_keep = ['Player', 'Date'] + [col for col in stat_fields if stat_inputs[col] > 0]
                temp_filtered = temp[[c for c in cols_to_keep if c in temp.columns]].copy()
                
                temp_filtered['Date'] = pd.to_datetime(temp_filtered['Date'], errors='coerce')
                temp_filtered = temp_filtered.sort_values(['Player', 'Date'], ascending=[True, False])
                temp_filtered = temp_filtered.groupby('Player').head(n_games)
                
                hit_mask = pd.Series([True] * len(temp_filtered), index=temp_filtered.index)
                for stat in stat_fields:
                    if stat_inputs[stat] > 0 and stat in temp_filtered.columns:
                        hit_mask = hit_mask & (temp_filtered[stat].astype(float) >= stat_inputs[stat])
                
                temp_filtered['Hit'] = hit_mask.astype(int)
                
                def calc_active_streak(series):
                    streak = 0
                    for val in series:
                        if val == 1:
                            streak += 1
                        else:
                            break
                    return streak

                agg_df = temp_filtered.groupby('Player').agg(
                    Hits=('Hit', 'sum'),
                    GamesPlayed=('Hit', 'count'),
                    ActiveStreak=('Hit', calc_active_streak)
                ).reset_index()
                
                agg_df = agg_df[agg_df['Hits'] > 0]
                
                if agg_df.empty:
                    st.write("No players found hitting these stats in the selected timeframe.")
                    return
                
                if not players_base_df.empty:
                    agg_df = agg_df.merge(players_base_df[['Player', 'Pos', 'Age', 'Current Team', 'YOS']], on='Player', how='left')
                else:
                    for col in ['Pos', 'Age', 'Current Team', 'YOS']:
                        agg_df[col] = ''
                
                agg_df['IsHotStreak'] = agg_df['ActiveStreak'] >= 3
                agg_df['LastName'] = agg_df['Player'].apply(lambda n: n.split(' ')[-1] if isinstance(n, str) and ' ' in n else n)
                agg_df = agg_df.sort_values(['IsHotStreak', 'Hits', 'LastName'], ascending=[False, False, True]).head(10)
                
                agg_df['Player'] = agg_df.apply(lambda r: f"🔥 {r['Player']}" if r['IsHotStreak'] else r['Player'], axis=1)
                agg_df['Hit Rate'] = agg_df.apply(lambda r: f"{r['Hits']} / {r['GamesPlayed']}", axis=1)
                
                display_cols = ['Player', 'Pos', 'Age', 'Current Team', 'YOS', 'ActiveStreak', 'Hit Rate']
                display_df = agg_df[display_cols].copy()
                display_df.rename(columns={'ActiveStreak': 'Active Streak'}, inplace=True)
                
                try:
                    def highlight_hot(val):
                        return 'background-color: rgba(249, 115, 22, 0.15)' if isinstance(val, str) and '🔥' in val else ''
                    
                    try:
                        styled_df = display_df.style.map(highlight_hot, subset=['Player'])
                    except AttributeError:
                        styled_df = display_df.style.applymap(highlight_hot, subset=['Player'])
                        
                    styled_df = styled_df.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+5)', props=[('text-align', 'left')]), # Text cols left-aligned
                        dict(selector='th:nth-child(-n+5)', props=[('text-align', 'left')])
                    ])
                        
                    event = st.dataframe(
                        styled_df,
                        width='stretch',
                        hide_index=True,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    if event and hasattr(event, 'selection') and hasattr(event.selection, 'rows') and len(event.selection.rows) > 0:
                        row_idx = event.selection.rows[0]
                        clean_name = display_df.iloc[row_idx]['Player'].replace('🔥 ', '').strip()
                        
                        player_details = temp[temp['Player'] == clean_name].copy()
                        player_details['Date'] = pd.to_datetime(player_details['Date'], errors='coerce')
                        player_details = player_details.sort_values('Date', ascending=False).head(n_games)
                        show_player_logs_dialog(clean_name, player_details, title)

                except Exception as e:
                    st.dataframe(display_df, width='stretch', hide_index=True)

            # Tabbed Interface for Games Summary
            st.markdown('---')
            tab5, tab10, tab20 = st.tabs(["📊 Last 5 Games", "📈 Last 10 Games", "🏆 Last 20 Games"])
            
            with tab5:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_5, 'Last 5 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 5, 'Last 5 Games')
                    
            with tab10:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_10, 'Last 10 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 10, 'Last 10 Games')
                    
            with tab20:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_20, 'Last 20 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 20, 'Last 20 Games')

except Exception as e:
    st.error(f"An error occurred while running the app: {e}")
    st.text(traceback.format_exc())
