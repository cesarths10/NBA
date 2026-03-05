import streamlit as st
import traceback

st.set_page_config(layout="wide", page_title="NBA Player Game Logs")

st.markdown("""
<style>
/* Streamlit Native Dataframes */
[data-testid="stDataFrame"] th {
    text-align: left !important;
}
[data-testid="stDataFrame"] td {
    text-align: left !important;
}

/* AgGrid Dataframes */
.ag-header-cell-label {
    justify-content: flex-start !important;
}
.ag-right-aligned-header .ag-header-cell-label {
    justify-content: flex-start !important;
}
.ag-right-aligned-cell {
    text-align: left !important;
}
.ag-cell {
    text-align: left !important;
}
</style>
""", unsafe_allow_html=True)

try:
    import pandas as pd
    from datetime import datetime
    from st_aggrid import AgGrid, JsCode
    from st_aggrid.grid_options_builder import GridOptionsBuilder
    import os
    import sqlite3
    import nba_logger as logger
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
            logger.log_login(user)
            st.rerun()
        else:
            st.session_state["password_correct"] = False

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not found or password incorrect")
        
    return False

try:
    if check_password():
        # Load gamelogs table from local SQLite database into a DataFrame
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

            # Session state initialization and helper callbacks to manage progressive inputs
            if 'player_search' not in st.session_state:
                st.session_state.player_search = ''
            if 'num_games_input' not in st.session_state:
                st.session_state.num_games_input = None
            if 'should_load' not in st.session_state:
                st.session_state.should_load = False

            def on_player_search_change():
                # Reset number-of-games input and loading flag when player search changes
                st.session_state.num_games_input = None
                st.session_state.should_load = False

            def on_num_change():
                # Validate numeric input and set should_load when a valid count is entered
                try:
                    val = int(st.session_state.num_games_input)
                    if val >= 1:
                        st.session_state.should_load = True
                    else:
                        st.session_state.should_load = False
                except Exception:
                    st.session_state.should_load = False

            # Sidebar UI: player selection and season filtering configuration
            all_players = sorted(df['Player'].unique())

            # Mapping season labels to official regular-season start dates for preseason exclusion
            season_start_dates = {
                '2025-26': datetime(2025, 10, 21),
                '2024-25': datetime(2024, 10, 24),
                '2023-24': datetime(2023, 10, 24),
                '2022-23': datetime(2022, 10, 18),
                '2021-22': datetime(2021, 10, 19),
                '2020-21': datetime(2020, 12, 22),
                '2019-20': datetime(2019, 10, 22),
                '2018-19': datetime(2018, 10, 16),
                '2017-18': datetime(2017, 10, 17),
                '2016-17': datetime(2016, 10, 25),
            }

            all_season_labels = list(season_start_dates.keys())
            # Mode toggle
            view_mode = st.sidebar.radio('View Mode', ['Select Player', 'Select Stat'])
            
            # Season selector
            selected_seasons = st.sidebar.multiselect('Select Season(s)', all_season_labels, default=all_season_labels[:1] if all_season_labels else [])
            
            selected_player = None
            if view_mode == 'Select Player':
                selected_player = st.sidebar.selectbox('Select Player', all_players, key='player_select')

            # We need df_filtered for both modes, but filtered based on seasons
            # Add season label & preseason indicator to all dataframe if not already there
            # Since processing the entire dataframe might be slow, let's optimize it.
            # But the user asked to compute it quickly. For "Select Stat", we need season filter applied to everyone.
            
            # Helper: map date series to season label
            def apply_seasons(target_df):
                if 'season_label' not in target_df.columns:
                    date_series = pd.to_datetime(target_df['Date'], errors='coerce')
                    def label_for_date(d):
                        if pd.isna(d):
                            return None
                        season_end = d.year + 1 if d.month >= 8 else d.year
                        return f"{season_end-1}-{str(season_end)[-2:]}"
                    target_df['season_label'] = date_series.apply(label_for_date)
                    
                    target_df['is_preseason'] = False
                    for lbl, start in season_start_dates.items():
                        mask_pre = (target_df['season_label'] == lbl) & (pd.to_datetime(target_df['Date'], errors='coerce') < start)
                        target_df.loc[mask_pre, 'is_preseason'] = True
                return target_df

            # Apply seasons to the main df to allow global filtering for "Select Stat"
            df = apply_seasons(df)

            df_filtered = pd.DataFrame()
            if view_mode == 'Select Player' and selected_player:
                player_df = df[df['Player'] == selected_player].copy()
                if selected_seasons:
                    df_filtered = player_df[(player_df['season_label'].isin(selected_seasons)) & (~player_df['is_preseason'])]
                else:
                    recent_season = player_df['season_label'].dropna().unique()
                    recent_season = sorted(recent_season)[-1] if len(recent_season) > 0 else None
                    if recent_season:
                        df_filtered = player_df[(player_df['season_label'] == recent_season) & (~player_df['is_preseason'])]
                    else:
                        df_filtered = player_df[~player_df['is_preseason']]

            elif view_mode == 'Select Stat':
                # Filter the whole DF by season
                if selected_seasons:
                    df_filtered = df[(df['season_label'].isin(selected_seasons)) & (~df['is_preseason'])].copy()
                else:
                    df_filtered = df[~df['is_preseason']].copy()
            else:
                df_filtered = pd.DataFrame()

            # Compute the player_stats DataFrame sections and show header info
            st.title('NBA Player Game Logs')
            
            if view_mode == 'Select Player':
                if selected_player:
                    st.subheader(f"{selected_player}")
                    st.write("Showing summary stats for Last 5, Last 10, and Last 20 games (prior seasons included if selected).")
                else:
                    st.subheader("No player loaded")
                    st.write("Select a player in the sidebar to show Last 5/10/20 game summaries.")
            else:
                st.subheader("Select Stat View")
                st.write("Showing the Top 10 players who hit the selected stats in their Last 5, 10, and 20 games.")


            # Prepare the set of columns to display and format dates/percent columns for presentation
            # Columns for the detailed rows (used in the grids)
            columns_to_display = [
                'Date', 'Opponent', 'WL', 'Status', 'Pos', 'MIN',
                'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                'P|R|A', 'P|A', 'P|R'
            ]
            # Keep only available columns in the original order using the filtered player dataframe
            display_cols = [c for c in columns_to_display if c in df_filtered.columns]
            # We'll construct three display DataFrames for 5/10/20 using df_filtered
            def make_display_df(df_source, n):
                if df_source.empty:
                    return pd.DataFrame(columns=columns_to_display)
                temp = df_source.sort_values('Date', ascending=False).head(n).copy()
                temp['Date'] = pd.to_datetime(temp['Date'], errors='coerce')
                # Compute combined columns if present
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].astype(float).sum(axis=1)
                # Format date
                if 'Date' in temp.columns:
                    temp['Date'] = temp['Date'].dt.strftime('%Y-%m-%d')
                # Format percent-like columns
                for col in ['FGPercent', 'TPPercent', 'FTPercent', 'FIC']:
                    if col in temp.columns:
                        temp[col] = temp[col].apply(lambda x: f'{x:.3f}' if pd.notnull(x) else '')
                return temp[columns_to_display].copy()

            display_5 = make_display_df(df_filtered, 5)
            display_10 = make_display_df(df_filtered, 10)
            display_20 = make_display_df(df_filtered, 20)

            import math

            stat_fields = ['PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']

            # Create stat filter UI (single set of inputs that apply to all three tables)
            stat_inputs = {}
            st.markdown('---')
            st.subheader('Stat Filters (applies to all three tables)')
            for stat in stat_fields:
                if f'stat_{stat}' not in st.session_state:
                    st.session_state[f'stat_{stat}'] = None

            if st.button('Clear Filters'):
                for stat in stat_fields:
                    st.session_state[f'stat_{stat}'] = None

            cols = st.columns(len(stat_fields))
            for i, stat in enumerate(stat_fields):
                # Omit 'value' explicitly to let Streamlit's 'key' attribute manage the state fully without looping
                val = cols[i].number_input(f"{stat}", min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                stat_inputs[stat] = val if val is not None else 0
            
            # Dialog logic for Popup Tables
            try:
                @st.dialog("Player Game Logs")
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.write(f"Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Opponent', 'WL', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = df_out['Date'].dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    st.dataframe(df_out, hide_index=True)
            except AttributeError:
                # Fallback if st.dialog is not available in this Streamlit version
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.markdown(f"### Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Opponent', 'WL', 'MIN', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = df_out['Date'].dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    st.dataframe(df_out, hide_index=True)

            # We want to display the stat filters BEFORE the tables if we are in Select Stat mode, 
            # and we effectively already did.


            # Helper to compute percent-hits for a display df
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

            # Render three tables with their percent summaries
            def render_table_with_summary(display_df_local, title):
                st.markdown('---')
                st.write(f"### {title}")
                # compute percent hits
                percents = compute_percent_hits(display_df_local)
                percent_cols = st.columns(len(stat_fields))
                for i, stat in enumerate(stat_fields):
                    if percents[stat] is not None:
                        percent_str = f"{percents[stat]:.1f}%"
                    else:
                        percent_str = "-"
                    # Display simplified label: 'STAT: X%'
                    percent_cols[i].markdown(f"**{stat}:** {percent_str}")

                # Use native Streamlit styled dataframe to prevent AgGrid header scrolling separation bugs
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
                            
                            highlight.append('background-color: #b6fcb6' if row_highlight else '')
                        return pd.DataFrame([highlight]*len(s.columns)).T
                    
                    styled = display_df_local.style.set_properties(**{'text-align': 'left'}).set_table_styles([dict(selector='th', props=[('text-align', 'left')])]).apply(lambda _: highlight_rows(display_df_local), axis=None)
                    st.dataframe(styled, use_container_width=True, hide_index=True)
                except Exception:
                    st.dataframe(display_df_local, use_container_width=True, hide_index=True)

            # Render logic for 'Select Stat'
            def render_stat_summary(df_all, players_base_df, n_games, title):
                st.markdown('---')
                st.write(f"### {title}")
                
                # Check if any stat inputs are greater than 0
                has_active_filters = any(stat_inputs[s] > 0 for s in stat_fields)
                if not has_active_filters:
                    st.info("Input a stat filter above to see top players.")
                    return
                
                # For each player, sort by date, take top n_games, add custom combos, count hits
                if df_all.empty:
                    st.write("No gamelogs available.")
                    return
                
                # We need combo columns for the entire dataframe just in case
                temp = df_all.copy()
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].astype(float).sum(axis=1)

                # Keep only fields we are filtering on to save memory
                cols_to_keep = ['Player', 'Date'] + [col for col in stat_fields if stat_inputs[col] > 0]
                temp = temp[[c for c in cols_to_keep if c in temp.columns]]
                
                # Filter down to top n_games per player
                temp['Date'] = pd.to_datetime(temp['Date'], errors='coerce')
                temp = temp.sort_values(['Player', 'Date'], ascending=[True, False])
                temp = temp.groupby('Player').head(n_games)
                
                # Count hits
                # A row is a hit if for ALL active stat inputs, the row matches or exceeds the value.
                # Actually, requirement: "hit the stat lines selected or greater".
                # It means ALL selected criteria must be met in that single game.
                hit_mask = pd.Series([True] * len(temp), index=temp.index)
                for stat in stat_fields:
                    if stat_inputs[stat] > 0 and stat in temp.columns:
                        hit_mask = hit_mask & (temp[stat].astype(float) >= stat_inputs[stat])
                
                temp['Hit'] = hit_mask.astype(int)
                
                # Aggregate
                def calc_active_streak(series):
                    streak = 0
                    for val in series:
                        if val == 1:
                            streak += 1
                        else:
                            break
                    return streak

                agg_df = temp.groupby('Player').agg(
                    Hits=('Hit', 'sum'),
                    GamesPlayed=('Hit', 'count'),
                    ActiveStreak=('Hit', calc_active_streak)
                ).reset_index()
                
                # Filter out those with 0 hits
                agg_df = agg_df[agg_df['Hits'] > 0]
                
                if agg_df.empty:
                    st.write("No players found hitting these stats in the selected timeframe.")
                    return
                
                # Merge with base data
                if not players_base_df.empty:
                    agg_df = agg_df.merge(players_base_df[['Player', 'Pos', 'Age', 'Current Team', 'YOS']], on='Player', how='left')
                else:
                    for col in ['Pos', 'Age', 'Current Team', 'YOS']:
                        agg_df[col] = ''
                
                # Calculate hot streak (>= 3 consecutive active games from latest)
                agg_df['IsHotStreak'] = agg_df['ActiveStreak'] >= 3
                
                # Extract last name for sorting
                agg_df['LastName'] = agg_df['Player'].apply(lambda n: n.split(' ')[-1] if isinstance(n, str) and ' ' in n else n)
                
                # Sort: Hot Streaks first, then Hits descending, LastName ascending
                agg_df = agg_df.sort_values(['IsHotStreak', 'Hits', 'LastName'], ascending=[False, False, True]).head(10)
                
                # Format for display
                # Add 🔥 icon to player name if Hot Streak
                agg_df['Player'] = agg_df.apply(lambda r: f"🔥 {r['Player']}" if r['IsHotStreak'] else r['Player'], axis=1)
                
                # Format Hits column
                agg_df['Hit Rate'] = agg_df.apply(lambda r: f"{r['Hits']} / {r['GamesPlayed']}", axis=1)
                
                display_cols = ['Player', 'Pos', 'Age', 'Current Team', 'YOS', 'ActiveStreak', 'Hit Rate']
                display_df = agg_df[display_cols].copy()
                display_df.rename(columns={'ActiveStreak': 'Active Streak'}, inplace=True)
                
                # Styling
                def color_hot_streaks(val):
                    # We can use the presence of 🔥 to determine the row or just style pandas dataframe
                    return 'background-color: rgba(255, 165, 0, 0.3)' if isinstance(val, str) and '🔥' in val else ''
                
                try:
                    # Aggrid is better, but row styling based on column value requires JS
                    js_hot_streak = """
                    function(params) {
                      if (params.data.Player && params.data.Player.includes('🔥')) {
                        return { backgroundColor: 'rgba(255,165,0,0.3)' };
                      }
                      return {};
                    }
                    """
                    gb = GridOptionsBuilder.from_dataframe(display_df)
                    gb.configure_default_column(minWidth=80, cellStyle={'textAlign': 'left'}, headerClass='left-aligned-header')
                    for col in display_df.columns:
                        gb.configure_column(col, type=[], cellStyle={'textAlign': 'left'})
                    gb.configure_grid_options(getRowStyle=JsCode(js_hot_streak))
                    gb.configure_selection(selection_mode="single", use_checkbox=False)
                    grid_options = gb.build()
                    row_height = 40
                    n_rows = len(display_df)
                    grid_height = min(2000, 60 + n_rows * row_height)
                    grid_response = AgGrid(
                        display_df,
                        gridOptions=grid_options,
                        enable_enterprise_modules=False,
                        theme='streamlit',
                        allow_unsafe_jscode=True,
                        update_on=['selectionChanged'],
                        height=grid_height,
                        # Append the stat filters to the key so the component entirely regenerates when filters change,
                        # successfully clearing any lingering selected_rows state and preventing ghost popups.
                        key=f"grid_stat_{title.replace(' ', '_')}_{'_'.join(str(v) for v in stat_inputs.values())}"
                    )
                    
                    if grid_response['selected_rows'] is not None and len(grid_response['selected_rows']) > 0:
                        import json
                        # selected_rows might be a dataframe in newer st_aggrid, but usually a list of dicts.
                        rows = grid_response['selected_rows']
                        selected_row = rows.iloc[0] if isinstance(rows, pd.DataFrame) else rows[0]
                        p_name = selected_row.get('Player', '') if isinstance(selected_row, dict) else selected_row['Player']
                        clean_name = p_name.replace('🔥 ', '').strip()
                        
                        player_details = temp[temp['Player'] == clean_name]
                        show_player_logs_dialog(clean_name, player_details, title)

                except Exception as e:
                    # Fallback to standard dataframe if AgGrid fails
                    st.dataframe(display_df, width='stretch')

            # Render each summary table depending on view_mode
            if view_mode == 'Select Player':
                render_table_with_summary(display_5, 'Last 5 Games')
                render_table_with_summary(display_10, 'Last 10 Games')
                render_table_with_summary(display_20, 'Last 20 Games')
            else:
                render_stat_summary(df_filtered, players_df, 5, 'Last 5 Games')
                render_stat_summary(df_filtered, players_df, 10, 'Last 10 Games')
                render_stat_summary(df_filtered, players_df, 20, 'Last 20 Games')

except Exception as e:
    st.error(f"An error occurred while running the app: {e}")
    # Optional: print traceback
    import traceback
    st.text(traceback.format_exc())

