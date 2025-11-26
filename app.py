import streamlit as st
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder

# Configure Streamlit layout to use the full browser width
st.set_page_config(layout='wide')

import logger

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        user = st.session_state.get("username_input", "")
        pwd = st.session_state.get("password_input", "")
        
        if "users" in st.secrets and user in st.secrets["users"] and st.secrets["users"][user] == pwd:
            st.session_state["password_correct"] = True
            del st.session_state["password_input"]  # don't store password
            # Log the login
            logger.log_login(user)
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show inputs
    st.text_input("Username", key="username_input")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password_input"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not found or password incorrect")
        
    return False

if check_password():
    # Load gamelogs table from local SQLite database into a DataFrame
    import sqlite3
    conn = sqlite3.connect('gamelogs.db')
    df = pd.read_sql_query('SELECT * FROM gamelogs', conn)
    conn.close()


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
    # Season selector and player picker
    selected_seasons = st.sidebar.multiselect('Select Season(s)', all_season_labels, default=all_season_labels[:1] if all_season_labels else [])
    selected_player = st.sidebar.selectbox('Select Player', all_players, key='player_select')

    # We'll always show the three summary tables (last 5/10/20) for the selected player
    if selected_player:
        # Prepare player dataframe and season_label + preseason flags once
        player_df = df[df['Player'] == selected_player].copy()
        date_series = pd.to_datetime(player_df['Date'], errors='coerce')
        def label_for_date(d):
            if pd.isna(d):
                return None
            season_end = d.year + 1 if d.month >= 8 else d.year
            return f"{season_end-1}-{str(season_end)[-2:]}"

        player_df['season_label'] = date_series.apply(label_for_date)
        player_df['is_preseason'] = False
        for lbl, start in season_start_dates.items():
            mask_pre = (player_df['season_label'] == lbl) & (pd.to_datetime(player_df['Date'], errors='coerce') < start)
            player_df.loc[mask_pre, 'is_preseason'] = True

        # When season filters are selected, prefer those; otherwise default to the most recent season
        if selected_seasons:
            df_filtered = player_df[(player_df['season_label'].isin(selected_seasons)) & (~player_df['is_preseason'])]
        else:
            # prioritize the most recent season only
            recent_season = player_df['season_label'].dropna().unique()
            recent_season = sorted(recent_season)[-1] if len(recent_season) > 0 else None
            if recent_season:
                df_filtered = player_df[(player_df['season_label'] == recent_season) & (~player_df['is_preseason'])]
            else:
                df_filtered = player_df[~player_df['is_preseason']]
    else:
        df_filtered = pd.DataFrame()

    # Compute the player_stats DataFrame sections and show header info
    st.title('NBA Player Game Logs')
    if selected_player:
        st.subheader(f"{selected_player}")
        # Note: we're showing three summaries below
        st.write("Showing summary stats for Last 5, Last 10, and Last 20 games (prior seasons included if selected).")
    else:
        st.subheader("No player loaded")
        st.write("Select a player in the sidebar to show Last 5/10/20 game summaries.")

    # Prepare the set of columns to display and format dates/percent columns for presentation
    # Columns for the detailed rows (used in the grids)
    columns_to_display = [
        'Date', 'Opponent', 'WL', 'Status', 'Pos', 'MIN',
        'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV',
        'PTS|REB|AST', 'PTS|AST', 'PTS|REB'
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
        for combo, parts in [('PTS|REB|AST', ['PTS', 'REB', 'AST']), ('PTS|AST', ['PTS', 'AST']), ('PTS|REB', ['PTS', 'REB'])]:
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

    stat_fields = ['PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PTS|REB|AST', 'PTS|AST', 'PTS|REB']

    # Create stat filter UI (single set of inputs that apply to all three tables)
    stat_inputs = {}
    st.markdown('---')
    st.subheader('Stat Filters (applies to all three tables)')
    for stat in stat_fields:
        if f'stat_{stat}' not in st.session_state:
            st.session_state[f'stat_{stat}'] = 0

    if st.button('Clear Filters'):
        for stat in stat_fields:
            st.session_state[f'stat_{stat}'] = 0

    cols = st.columns(len(stat_fields))
    for i, stat in enumerate(stat_fields):
        stat_inputs[stat] = cols[i].number_input(f"{stat}", min_value=0, value=st.session_state[f'stat_{stat}'], step=1, key=f'stat_{stat}')

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

    # Helper to get row-style for AgGrid JS
    def make_getRowStyle_js():
        js = "function(params) {\\n  const fields = ['PTS','TPM','REB','AST','STL','BLK','TOV','PTS|REB|AST','PTS|AST','PTS|REB'];\\n  const inputs = {" + ",".join([f"'{stat}': {stat_inputs[stat]}" for stat in stat_fields]) + "};\\n  for (let i = 0; i < fields.length; i++) {\\n    let stat = fields[i];\\n    let val = params.data[stat];\\n    if (inputs[stat] > 0 && val !== undefined && val !== null && Number(val) >= inputs[stat]) {\\n      return { backgroundColor: '#b6fcb6' };\\n    }\\n  }\\n  return {};\\n}"
        return js

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

        # Display table using AgGrid where possible, falling back to pandas styling
        try:
            gb = GridOptionsBuilder.from_dataframe(display_df_local)
            for col in gb.column_definitions:
                col['flex'] = 1
                col['minWidth'] = 80
                col['cellStyle'] = {'textAlign': 'left'}
                col['headerClass'] = 'left-aligned-header'
            gb.configure_grid_options(getRowStyle=make_getRowStyle_js())
            grid_options = gb.build()
            row_height = 40
            n_rows = len(display_df_local)
            grid_height = min(2000, 60 + n_rows * row_height)
            AgGrid(
                display_df_local,
                gridOptions=grid_options,
                enable_enterprise_modules=False,
                theme='streamlit',
                allow_unsafe_jscode=True,
                update_mode='NO_UPDATE',
                height=grid_height,
            )
        except Exception:
            try:
                def highlight_rows(s):
                    highlight = []
                    for idx, row in s.iterrows():
                        row_highlight = False
                        for stat in stat_fields:
                            if stat in row and stat_inputs[stat] > 0 and not pd.isnull(row[stat]):
                                try:
                                    if float(row[stat]) >= stat_inputs[stat]:
                                        row_highlight = True
                                except Exception:
                                    continue
                        highlight.append('background-color: #b6fcb6' if row_highlight else '')
                    return pd.DataFrame([highlight]*len(s.columns)).T
                styled = display_df_local.style.set_properties(**{'text-align': 'left'}).apply(lambda _: highlight_rows(display_df_local), axis=None)
                st.dataframe(styled, width='stretch')
            except Exception:
                st.dataframe(display_df_local, width='stretch')

    # Render each summary table
    render_table_with_summary(display_5, 'Last 5 Games')
    render_table_with_summary(display_10, 'Last 10 Games')
    render_table_with_summary(display_20, 'Last 20 Games')
