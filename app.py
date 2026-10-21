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

/* Success rate scorecard styling */
.success-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.9));
    backdrop-filter: blur(12px);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    margin-top: 1rem;
    margin-bottom: 1.5rem;
}
.kpi-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: 13px;
    text-align: center;
}
.kpi-chip-green {
    background-color: rgba(16, 185, 129, 0.15);
    color: #065f46;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
.kpi-chip-amber {
    background-color: rgba(245, 158, 11, 0.15);
    color: #92400e;
    border: 1px solid rgba(245, 158, 11, 0.35);
}
.kpi-chip-red {
    background-color: rgba(239, 68, 68, 0.12);
    color: #991b1b;
    border: 1px solid rgba(239, 68, 68, 0.3);
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

        def file_mtime(path):
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
        def load_players_data(path, mtime):
            if not os.path.exists(path):
                return pd.DataFrame()
            try:
                if path.endswith(".csv"):
                    return pd.read_csv(path)
                return pd.read_excel(path)
            except Exception as e:
                st.error(f"Error reading {path}: {e}")
                return pd.DataFrame()

        PLAYERS_PATH = "players.csv" if os.path.exists("players.csv") else "players.xlsx"

        df = load_gamelogs(DB_PATH, file_mtime(DB_PATH))
        players_df = load_players_data(PLAYERS_PATH, file_mtime(PLAYERS_PATH))

        if df.empty:
            st.warning("No data found in gamelogs.db or database file is missing.")
        else:
            all_players = sorted(df['Player'].unique())

            # Sidebar selectors
            st.sidebar.markdown("## 📊 Navigation & Filters")
            view_mode = st.sidebar.radio('View Mode', ['Select Player', 'Select Stat'])
            
            # Season selector with full 4-digit year formatting (e.g. 2026-2027)
            import re
            def format_season_display(s: str) -> str:
                if not isinstance(s, str):
                    return ""
                m = re.match(r"^(\d{4})-(\d{2})$", s.strip())
                if m:
                    y1, y2 = m.groups()
                    full_label = f"{y1}-20{y2}"
                    if s == "2026-27":
                        return f"{full_label} (Current Season)"
                    return full_label
                return s

            raw_seasons = sorted(df['season_label'].dropna().unique(), reverse=True)
            season_display_map = {format_season_display(s): s for s in raw_seasons}
            display_options = list(season_display_map.keys())

            # Default to current season (2026-2027) on open
            default_display = [display_options[0]] if display_options else []
            selected_display_seasons = st.sidebar.multiselect(
                'Select Season(s)',
                display_options,
                default=default_display
            )
            selected_seasons = [season_display_map[d] for d in selected_display_seasons if d in season_display_map]
            
            # Game Type selector
            all_game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
            selected_game_types = st.sidebar.multiselect(
                'Select Game Type(s)',
                all_game_types,
                default=['Regular Season', 'Playoffs', 'Preseason']
            )

            # Rookie identification from players_df (YOS == 0)
            rookie_names = set()
            if not players_df.empty and 'YOS' in players_df.columns:
                rookie_mask = (players_df['YOS'].astype(str).str.strip() == '0') | (players_df['YOS'].astype(str).str.upper().str.strip() == 'R')
                rookie_names = set(players_df[rookie_mask]['Player'].dropna().unique())

            # Combined universe of players (database + roster)
            db_players = set(df['Player'].dropna().unique())
            csv_players = set(players_df['Player'].dropna().unique()) if not players_df.empty else set()
            all_known_players = sorted(list(db_players.union(csv_players)))

            # Player Pool Selector
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 👥 Player Pool")
            player_pool = st.sidebar.radio(
                'Filter by Class',
                ['All Players', '⭐ 2026 Rookie Class', 'Veterans Only'],
                index=0,
                key='player_pool_select'
            )

            # Filter selectable players based on pool
            if player_pool == '⭐ 2026 Rookie Class':
                available_players = [p for p in all_known_players if p in rookie_names]
            elif player_pool == 'Veterans Only':
                available_players = [p for p in all_known_players if p not in rookie_names]
            else:
                available_players = all_known_players

            selected_player = None
            if view_mode == 'Select Player':
                if not available_players:
                    st.sidebar.warning("No players found in this pool.")
                else:
                    selected_player = st.sidebar.selectbox(
                        'Select Player',
                        available_players,
                        format_func=lambda p: f"⭐ {p} (Rookie)" if p in rookie_names else p,
                        key='player_select'
                    )

            # Filter data based on sidebar settings
            df_filtered = df.copy()
            if selected_seasons:
                df_filtered = df_filtered[df_filtered['season_label'].isin(selected_seasons)]
            if selected_game_types:
                df_filtered = df_filtered[df_filtered['GameType'].isin(selected_game_types)]

            # Filter Leaderboard by Player Pool
            if view_mode == 'Select Stat':
                if player_pool == '⭐ 2026 Rookie Class':
                    df_filtered = df_filtered[df_filtered['Player'].isin(rookie_names)]
                elif player_pool == 'Veterans Only':
                    df_filtered = df_filtered[~df_filtered['Player'].isin(rookie_names)]

            if view_mode == 'Select Player' and selected_player:
                df_filtered = df_filtered[df_filtered['Player'] == selected_player]

            st.title('NBA Player Game Logs')
            
            if view_mode == 'Select Player':
                if selected_player:
                    is_rookie = selected_player in rookie_names
                    rookie_tag = " <span style='font-size: 13px; background: rgba(245, 158, 11, 0.15); color: #d97706; border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px 8px; border-radius: 6px; font-weight: 600;'>⭐ 2026 Rookie Class</span>" if is_rookie else ""
                    st.markdown(f"### 🏀 {selected_player}{rookie_tag}", unsafe_allow_html=True)
                    st.write("Showing summary stats and game logs for Last 5, Last 10, Last 20, and Full Season.")
                else:
                    st.subheader("No player loaded")
                    st.write("Select a player in the sidebar to show detailed summaries.")
            else:
                pool_title = " (2026 Rookie Class)" if player_pool == '⭐ 2026 Rookie Class' else (" (Veterans Only)" if player_pool == 'Veterans Only' else "")
                st.subheader(f"🏆 Leaderboard View{pool_title}")
                st.write("Showing the Top 10 players who hit the selected stats in their Last 5, 10, 20, or Full Season games.")

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

            def make_display_df(df_source, n=None):
                if df_source.empty:
                    return pd.DataFrame(columns=columns_to_display)
                if n is not None:
                    temp = df_source.sort_values('Date', ascending=False).head(n).copy()
                else:
                    temp = df_source.sort_values('Date', ascending=False).copy()
                
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
            display_season = make_display_df(df_filtered, None)

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
                if display_df_local.empty:
                    st.info(f"No game logs recorded for {title} in the selected season(s) and game type(s).")
                    return

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
                if n_games is not None:
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
                
                def format_lb_player(r):
                    base = r['Player']
                    prefix = "🔥 " if r['IsHotStreak'] else ""
                    if base in rookie_names:
                        prefix += "⭐ "
                    return f"{prefix}{base}"

                agg_df['Player'] = agg_df.apply(format_lb_player, axis=1)
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
                        clean_name = display_df.iloc[row_idx]['Player'].replace('🔥 ', '').replace('⭐ ', '').strip()
                        
                        player_details = temp[temp['Player'] == clean_name].copy()
                        player_details['Date'] = pd.to_datetime(player_details['Date'], errors='coerce')
                        if n_games is not None:
                            player_details = player_details.sort_values('Date', ascending=False).head(n_games)
                        else:
                            player_details = player_details.sort_values('Date', ascending=False)
                        show_player_logs_dialog(clean_name, player_details, title)

                except Exception as e:
                    st.dataframe(display_df, width='stretch', hide_index=True)

            # Success Rate Dashboard Panel
            active_stats = [stat for stat in stat_fields if stat_inputs.get(stat, 0) > 0]
            if view_mode == 'Select Player' and selected_player:
                if active_stats:
                    st.markdown('<div class="success-card">', unsafe_allow_html=True)
                    st.markdown("### 🎯 Target Success Rate Dashboard")
                    st.caption(f"Cross-referencing recent form (L5, L10, L20) against full season baseline for **{selected_player}**.")

                    def calc_stat_rate(df_sub, stat, target):
                        if df_sub.empty or stat not in df_sub.columns or target <= 0:
                            return None, 0, 0
                        vals = pd.to_numeric(df_sub[stat], errors='coerce').dropna()
                        if len(vals) == 0:
                            return None, 0, 0
                        hits = int((vals >= target).sum())
                        total = len(vals)
                        pct = (hits / total) * 100
                        return pct, hits, total

                    def format_kpi_badge(pct, hits, total):
                        if pct is None or total == 0:
                            return '<span style="color: #94a3b8;">-</span>'
                        if pct >= 70:
                            cls = "kpi-chip-green"
                        elif pct >= 50:
                            cls = "kpi-chip-amber"
                        else:
                            cls = "kpi-chip-red"
                        return f'<span class="kpi-chip {cls}">{pct:.1f}% ({hits}/{total})</span>'

                    dashboard_rows = []
                    for stat in active_stats:
                        t_val = stat_inputs[stat]
                        p5, h5, tot5 = calc_stat_rate(display_5, stat, t_val)
                        p10, h10, tot10 = calc_stat_rate(display_10, stat, t_val)
                        p20, h20, tot20 = calc_stat_rate(display_20, stat, t_val)
                        ps, hs, tots = calc_stat_rate(display_season, stat, t_val)

                        b5 = format_kpi_badge(p5, h5, tot5)
                        b10 = format_kpi_badge(p10, h10, tot10)
                        b20 = format_kpi_badge(p20, h20, tot20)
                        bs = format_kpi_badge(ps, hs, tots)

                        # Trend calculation (L5 vs Full Season)
                        if p5 is not None and ps is not None and tot5 > 0 and tots > 0:
                            diff = p5 - ps
                            if diff >= 10:
                                trend = f'<span style="color: #059669; font-weight: 700;">🔥 Up (+{diff:.0f}%)</span>'
                            elif diff <= -10:
                                trend = f'<span style="color: #dc2626; font-weight: 700;">❄️ Down ({diff:.0f}%)</span>'
                            else:
                                trend = '<span style="color: #64748b; font-weight: 500;">⚖️ Steady</span>'
                        else:
                            trend = '<span style="color: #94a3b8;">-</span>'

                        stat_name = primary_labels.get(stat) or secondary_labels.get(stat) or dict(combo_stats).get(stat) or stat
                        dashboard_rows.append(f"""
                        <tr style="border-bottom: 1px solid rgba(226, 232, 240, 0.7);">
                            <td style="padding: 10px 12px; font-weight: 600;">{stat_name} <span style="color: #0284c7; font-weight: 700;">({t_val}+)</span></td>
                            <td style="padding: 10px 12px; text-align: center;">{b5}</td>
                            <td style="padding: 10px 12px; text-align: center;">{b10}</td>
                            <td style="padding: 10px 12px; text-align: center;">{b20}</td>
                            <td style="padding: 10px 12px; text-align: center;">{bs}</td>
                            <td style="padding: 10px 12px; text-align: center;">{trend}</td>
                        </tr>
                        """)

                    # Combo / Parlay row if multiple target stats active
                    if len(active_stats) >= 2:
                        def calc_parlay(df_sub):
                            if df_sub.empty:
                                return None, 0, 0
                            mask = pd.Series([True] * len(df_sub), index=df_sub.index)
                            for stat in active_stats:
                                if stat in df_sub.columns:
                                    mask = mask & (pd.to_numeric(df_sub[stat], errors='coerce') >= stat_inputs[stat])
                            hits = int(mask.sum())
                            total = len(df_sub)
                            pct = (hits / total) * 100 if total > 0 else 0
                            return pct, hits, total

                        cp5, ch5, ctot5 = calc_parlay(display_5)
                        cp10, ch10, ctot10 = calc_parlay(display_10)
                        cp20, ch20, ctot20 = calc_parlay(display_20)
                        cps, chs, ctots = calc_parlay(display_season)

                        cb5 = format_kpi_badge(cp5, ch5, ctot5)
                        cb10 = format_kpi_badge(cp10, ch10, ctot10)
                        cb20 = format_kpi_badge(cp20, ch20, ctot20)
                        cbs = format_kpi_badge(cps, chs, ctots)

                        dashboard_rows.append(f"""
                        <tr style="background: rgba(241, 245, 249, 0.85); font-weight: 700;">
                            <td style="padding: 12px; color: #4338ca;">🎯 ALL TARGETS (PARLAY HIT)</td>
                            <td style="padding: 12px; text-align: center;">{cb5}</td>
                            <td style="padding: 12px; text-align: center;">{cb10}</td>
                            <td style="padding: 12px; text-align: center;">{cb20}</td>
                            <td style="padding: 12px; text-align: center;">{cbs}</td>
                            <td style="padding: 12px; text-align: center;">-</td>
                        </tr>
                        """)

                    dashboard_table = f"""
                    <div style="overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                            <thead>
                                <tr style="border-bottom: 2px solid #cbd5e1; text-align: left; color: #475569;">
                                    <th style="padding: 8px 12px;">Target Stat Line</th>
                                    <th style="padding: 8px 12px; text-align: center;">Last 5 Games</th>
                                    <th style="padding: 8px 12px; text-align: center;">Last 10 Games</th>
                                    <th style="padding: 8px 12px; text-align: center;">Last 20 Games</th>
                                    <th style="padding: 8px 12px; text-align: center;">Full Season</th>
                                    <th style="padding: 8px 12px; text-align: center;">L5 vs. Season Trend</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(dashboard_rows)}
                            </tbody>
                        </table>
                    </div>
                    """
                    st.markdown(dashboard_table, unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
            elif view_mode == 'Select Stat' and active_stats:
                st.markdown('<div class="success-card">', unsafe_allow_html=True)
                st.markdown("### 🏆 Leaderboard Target Criteria")
                criteria_chips = []
                for s in active_stats:
                    lbl = primary_labels.get(s) or secondary_labels.get(s) or dict(combo_stats).get(s) or s
                    criteria_chips.append(f"<b>{lbl}:</b> {stat_inputs[s]}+")
                st.markdown(f"Evaluating players against: {' &nbsp;|&nbsp; '.join(criteria_chips)}", unsafe_allow_html=True)
                st.caption("Use the tabs below to view top players across Last 5, Last 10, Last 20, or Full Season.")
                st.markdown('</div>', unsafe_allow_html=True)

            # Tabbed Interface for Games Summary
            st.markdown('---')
            tab5, tab10, tab20, tab_season = st.tabs([
                "📊 Last 5 Games",
                "📈 Last 10 Games",
                "🏆 Last 20 Games",
                "📅 Full Season"
            ])
            
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

            with tab_season:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_season, 'Full Season')
                else:
                    render_stat_summary(df_filtered, players_df, None, 'Full Season')

except Exception as e:
    st.error(f"An error occurred while running the app: {e}")
    st.text(traceback.format_exc())
