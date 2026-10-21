import streamlit as st
import traceback

st.set_page_config(layout="wide", page_title="NBA Player Game Logs")

# Custom Styles for Sports-Betting Dark Theme Design System
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800;900&display=swap');

/* Global Font & Athletic Canvas */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #e2e8f0;
    font-feature-settings: "cv05" 1, "cv08" 1, "tnum" 1;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-rendering: optimizeLegibility;
}

/* Headings with Athletic Typography */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    color: #f8fafc !important;
    letter-spacing: -0.02em;
}

h1 {
    background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800 !important;
}

/* Obsidian Custom Scrollbars */
::-webkit-scrollbar {
    width: 7px;
    height: 7px;
}
::-webkit-scrollbar-track {
    background: #0b0f19;
}
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.14);
    border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(99, 102, 241, 0.45);
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background-color: #0d1322 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}
section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    background-color: rgba(19, 27, 46, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    transition: all 0.2s ease;
}
section[data-testid="stSidebar"] div[data-testid="stExpander"]:hover {
    border-color: rgba(99, 102, 241, 0.3) !important;
}
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 6px;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label {
    background: rgba(30, 41, 59, 0.45);
    border: 1px solid rgba(255, 255, 255, 0.07);
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
    font-size: 13px;
    font-weight: 600;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    border-color: rgba(99, 102, 241, 0.4);
    background: rgba(99, 102, 241, 0.15);
    transform: translateX(2px);
}

/* Native Container Cards with Smooth Elevation Lift */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(19, 27, 46, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 24px -4px rgba(0, 0, 0, 0.45);
    backdrop-filter: blur(14px);
    transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.22s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.22s ease !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(99, 102, 241, 0.35) !important;
    box-shadow: 0 12px 30px -4px rgba(0, 0, 0, 0.6), 0 0 18px rgba(99, 102, 241, 0.12) !important;
    transform: translateY(-1px);
}

/* Tab Bar Styling with Animated Underline */
div[data-baseweb="tab-list"] {
    gap: 10px;
    background-color: transparent;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 2px;
}
button[data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 9px 18px;
    font-weight: 600;
    font-family: 'Outfit', sans-serif;
    color: #94a3b8;
    background: transparent;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
button[data-baseweb="tab"]:hover {
    color: #f8fafc;
    background: rgba(255, 255, 255, 0.03);
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #818cf8 !important;
    border-bottom: 2px solid #6366f1 !important;
    text-shadow: 0 0 10px rgba(99, 102, 241, 0.4);
}

/* Input Fields with Ambient Focus */
div[data-testid="stNumberInput"] input {
    background-color: rgba(15, 23, 42, 0.75) !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    border-radius: 8px !important;
    color: #f8fafc !important;
    font-weight: 600 !important;
    transition: all 0.18s ease !important;
}
div[data-testid="stNumberInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.35), 0 0 12px rgba(99, 102, 241, 0.2) !important;
}

/* Primary Action Buttons */
div.stButton > button {
    border-radius: 8px;
    font-weight: 600;
    font-family: 'Outfit', sans-serif;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background-color: rgba(30, 41, 59, 0.6);
    color: #cbd5e1;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
}
div.stButton > button:hover {
    border-color: #6366f1;
    color: #a5b4fc;
    background-color: rgba(99, 102, 241, 0.18);
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.28);
    transform: translateY(-1px);
}
div.stButton > button:active {
    transform: translateY(0) scale(0.98);
}

/* Quick Prop Ladder Buttons (Nested Column Chips) */
div[data-testid="stColumn"] div[data-testid="stColumn"] div.stButton > button {
    padding: 2px 4px !important;
    min-height: 25px !important;
    height: 25px !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    border-radius: 6px !important;
    background-color: rgba(30, 41, 59, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #94a3b8 !important;
    line-height: 1 !important;
    transition: all 0.15s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
div[data-testid="stColumn"] div[data-testid="stColumn"] div.stButton > button:hover {
    border-color: #38bdf8 !important;
    color: #38bdf8 !important;
    background-color: rgba(56, 189, 248, 0.15) !important;
    box-shadow: 0 0 10px rgba(56, 189, 248, 0.3) !important;
    transform: translateY(-1px);
}
div[data-testid="stColumn"] div[data-testid="stColumn"] div.stButton > button:active {
    transform: translateY(0) scale(0.96);
}

/* Styled Metric Badges */
.metric-badge {
    background: rgba(30, 41, 59, 0.75);
    color: #f8fafc;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    display: inline-block;
    text-align: center;
    width: 100%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-badge:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-1px);
}

/* High-Contrast Sports KPI Chips */
.kpi-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 700;
    font-size: 13px;
    text-align: center;
    letter-spacing: 0.02em;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.kpi-chip:hover {
    transform: scale(1.04);
}
.kpi-chip-green {
    background-color: rgba(16, 185, 129, 0.18);
    color: #34d399;
    border: 1px solid rgba(52, 211, 153, 0.4);
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.15);
}
.kpi-chip-amber {
    background-color: rgba(245, 158, 11, 0.18);
    color: #fbbf24;
    border: 1px solid rgba(251, 191, 36, 0.4);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.15);
}
.kpi-chip-red {
    background-color: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border: 1px solid rgba(248, 113, 113, 0.4);
}

/* Live Database Pulsing Indicator */
@keyframes live-pulse {
    0%, 100% {
        opacity: 1;
        transform: scale(1);
        box-shadow: 0 0 8px #34d399;
    }
    50% {
        opacity: 0.55;
        transform: scale(0.85);
        box-shadow: 0 0 3px #34d399;
    }
}
.live-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #34d399;
    display: inline-block;
    animation: live-pulse 2s infinite ease-in-out;
}

/* Dataframe Container Aesthetics */
div[data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
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

            # Sleek Sidebar Branding & Navigation
            st.sidebar.markdown("""
            <div style="padding: 4px 0 16px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.08); margin-bottom: 16px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 24px;">⚡</span>
                    <div>
                        <span style="font-family: 'Outfit', sans-serif; font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em;">PropPulse</span>
                        <span style="background: rgba(99, 102, 241, 0.25); border: 1px solid rgba(99, 102, 241, 0.4); color: #a5b4fc; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">NBA PRO</span>
                    </div>
                </div>
                <div style="font-size: 11px; color: #94a3b8; margin-top: 5px; font-weight: 500;">Intelligence Dashboard • 2026-2027</div>
            </div>
            """, unsafe_allow_html=True)

            st.sidebar.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>📊 View Mode</span>", unsafe_allow_html=True)
            mode_labels = {
                'Select Player': '👤 Player Logs & Form',
                'Select Stat': '🏆 Prop Leaderboard'
            }
            view_mode = st.sidebar.radio(
                'View Mode',
                ['Select Player', 'Select Stat'],
                format_func=lambda m: mode_labels[m],
                label_visibility='collapsed'
            )

            # Collapsible Scope & Season Filters
            st.sidebar.write("")
            with st.sidebar.expander("⚙️ Scope & Season Filters", expanded=True):
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

                default_display = [display_options[0]] if display_options else []
                selected_display_seasons = st.multiselect(
                    'Select Season(s)',
                    display_options,
                    default=default_display
                )
                selected_seasons = [season_display_map[d] for d in selected_display_seasons if d in season_display_map]
                
                all_game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
                selected_game_types = st.multiselect(
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
            st.sidebar.write("")
            st.sidebar.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>👥 Player Universe</span>", unsafe_allow_html=True)
            player_pool = st.sidebar.radio(
                'Filter by Class',
                ['All Players', '⭐ 2026 Rookie Class', 'Veterans Only'],
                index=0,
                key='player_pool_select',
                label_visibility='collapsed'
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
                st.sidebar.write("")
                st.sidebar.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>🔍 Select Player</span>", unsafe_allow_html=True)
                if not available_players:
                    st.sidebar.warning("No players found in this pool.")
                else:
                    selected_player = st.sidebar.selectbox(
                        'Select Player',
                        available_players,
                        format_func=lambda p: f"⭐ {p} (Rookie)" if p in rookie_names else p,
                        key='player_select',
                        label_visibility='collapsed'
                    )

            # Sidebar Database Telemetry Card
            st.sidebar.markdown("---")
            st.sidebar.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 14px; font-size: 12px; color: #94a3b8;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span>📦 Database</span> <b style="color: #f1f5f9;">{len(df):,} Games</b>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                    <span>🏀 Active Roster</span> <b style="color: #f1f5f9;">{len(all_known_players):,} Players</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>⭐ 2026 Rookies</span> <b style="color: #fbbf24;">{len(rookie_names)} Tracked</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

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

            # Brand Header on Main Canvas
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 1rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 32px;">🏀</span>
                        <span style="font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 900; letter-spacing: -0.03em; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PROPPULSE NBA</span>
                        <span style="background: rgba(99, 102, 241, 0.2); border: 1px solid rgba(99, 102, 241, 0.4); color: #a5b4fc; font-size: 11px; font-weight: 800; padding: 3px 8px; border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.08em;">v2.6 PRO</span>
                    </div>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px; font-weight: 500;">Real-time Player Prop Analytics • Hit Rate Intelligence • Multi-Horizon Form</p>
                </div>
                <div style="text-align: right; display: flex; gap: 8px;">
                    <span style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; font-size: 12px; font-weight: 700; padding: 5px 12px; border-radius: 8px; display: inline-flex; align-items: center; gap: 8px;">
                        <span class="live-dot"></span> Live Database
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if view_mode == 'Select Player':
                if selected_player:
                    is_rookie = selected_player in rookie_names
                    rookie_tag = " <span style='font-size: 13px; background: rgba(245, 158, 11, 0.18); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.4); padding: 3px 10px; border-radius: 6px; font-weight: 700; box-shadow: 0 0 8px rgba(245, 158, 11, 0.15);'>⭐ 2026 Rookie Class</span>" if is_rookie else ""
                    st.markdown(f"### 🏀 {selected_player}{rookie_tag}", unsafe_allow_html=True)
                    st.caption("Detailed game logs and multi-timeframe target performance for Last 5, 10, 20, and Full Season.")
                else:
                    st.subheader("No player loaded")
                    st.caption("Select a player in the sidebar to show detailed summaries.")
            else:
                pool_title = " (2026 Rookie Class)" if player_pool == '⭐ 2026 Rookie Class' else (" (Veterans Only)" if player_pool == 'Veterans Only' else "")
                st.subheader(f"🏆 Prop Leaderboard{pool_title}")
                st.caption("Top 10 players ranked by hit rate and consistency across Last 5, 10, 20, or Full Season games.")

            columns_to_display = [
                'Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN',
                'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV',
                'P|R|A', 'P|A', 'P|R'
            ]
            stat_fields = ['PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']

            # Target Stat Line Filters Layout
            stat_inputs = {}
            with st.container(border=True):
                st.markdown("### 🔍 Target Stat Lines & Quick Prop Presets")
                st.caption("Select a popular betting preset or click milestone ladder chips to evaluate multi-horizon success rates.")

                stat_ladders = {
                    'PTS': [15, 20, 25, 30],
                    'TPM': [2, 3, 4],
                    'REB': [6, 8, 10],
                    'AST': [4, 6, 8],
                    'STL': [1, 2],
                    'BLK': [1, 2],
                    'TOV': [2, 3],
                    'P|R|A': [25, 30, 35],
                    'P|A': [20, 25],
                    'P|R': [20, 25]
                }

                # Quick Prop Presets Row
                preset_bar, clear_bar = st.columns([6, 1])
                with preset_bar:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>⚡ Popular Betting Presets:</span>", unsafe_allow_html=True)
                    p_cols = st.columns(7)
                    if p_cols[0].button("🏀 20+ PTS", use_container_width=True, help="Set Points to 20+"):
                        st.session_state['stat_PTS'] = 20
                        st.rerun()
                    if p_cols[1].button("🏀 25+ PTS", use_container_width=True, help="Set Points to 25+"):
                        st.session_state['stat_PTS'] = 25
                        st.rerun()
                    if p_cols[2].button("🎯 3+ 3PM", use_container_width=True, help="Set 3-Pointers to 3+"):
                        st.session_state['stat_TPM'] = 3
                        st.rerun()
                    if p_cols[3].button("💪 8+ REB", use_container_width=True, help="Set Rebounds to 8+"):
                        st.session_state['stat_REB'] = 8
                        st.rerun()
                    if p_cols[4].button("🤝 6+ AST", use_container_width=True, help="Set Assists to 6+"):
                        st.session_state['stat_AST'] = 6
                        st.rerun()
                    if p_cols[5].button("🔥 30+ PRA", use_container_width=True, help="Set PTS + REB + AST to 30+"):
                        st.session_state['stat_P|R|A'] = 30
                        st.rerun()
                    if p_cols[6].button("⭐ 10P/10R DD", use_container_width=True, help="Double-Double line: 10+ PTS & 10+ REB"):
                        st.session_state['stat_PTS'] = 10
                        st.session_state['stat_REB'] = 10
                        st.rerun()
                with clear_bar:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>Reset:</span>", unsafe_allow_html=True)
                    if st.button('🧹 Clear All', use_container_width=True, help="Reset all stat lines"):
                        for stat in stat_fields:
                            st.session_state[f'stat_{stat}'] = None
                        st.rerun()

                st.write("")

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
                    with row1[i]:
                        val = st.number_input(primary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                if l_cols[idx].button(f"{l_val}+", key=f"ladder_{stat}_{l_val}", use_container_width=True):
                                    st.session_state[f'stat_{stat}'] = l_val
                                    st.rerun()

                st.write("")

                # Row 2: Defensive & Combination Metrics
                row2 = st.columns(5)
                secondary_stats = ['BLK', 'TOV']
                secondary_labels = {
                    'BLK': '🛡️ Blocks',
                    'TOV': '⚠️ Turnovers'
                }
                for i, stat in enumerate(secondary_stats):
                    with row2[i]:
                        val = st.number_input(secondary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                if l_cols[idx].button(f"{l_val}+", key=f"ladder_{stat}_{l_val}", use_container_width=True):
                                    st.session_state[f'stat_{stat}'] = l_val
                                    st.rerun()

                combo_stats = [
                    ('P|R|A', '🔥 PTS + REB + AST'),
                    ('P|A', '🔥 PTS + AST'),
                    ('P|R', '🔥 PTS + REB')
                ]
                for i, (stat, label) in enumerate(combo_stats):
                    with row2[i + 2]:
                        val = st.number_input(label, min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                if l_cols[idx].button(f"{l_val}+", key=f"ladder_{stat}_{l_val}", use_container_width=True):
                                    st.session_state[f'stat_{stat}'] = l_val
                                    st.rerun()

            def get_gamelog_column_config():
                cfg = {
                    "Date": st.column_config.TextColumn("Date", width="small"),
                    "Team": st.column_config.TextColumn("Team", width="small"),
                    "Opponent": st.column_config.TextColumn("Opponent", width="small"),
                    "WL": st.column_config.TextColumn("WL", help="Game Outcome (W / L)", width="small"),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                    "Pos": st.column_config.TextColumn("Pos", width="small"),
                    "MIN": st.column_config.NumberColumn("MIN", format="%.0f", width="small")
                }
                for s in stat_fields:
                    target = stat_inputs.get(s, 0)
                    help_msg = f"Target: {target}+" if target > 0 else f"{s} Stat"
                    cfg[s] = st.column_config.NumberColumn(
                        s,
                        help=help_msg,
                        format="%.0f",
                        width="small"
                    )
                return cfg

            # Dialog Logic for Popup Game Logs
            try:
                @st.dialog("Player Game Logs")
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.write(f"Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN', 'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    if 'WL' in df_out.columns:
                        df_out['WL'] = df_out['WL'].apply(
                            lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                        )
                    st.dataframe(df_out, column_config=get_gamelog_column_config(), width='stretch', hide_index=True)
            except AttributeError:
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.markdown(f"### Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN', 'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    if 'WL' in df_out.columns:
                        df_out['WL'] = df_out['WL'].apply(
                            lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                        )
                    st.dataframe(df_out, column_config=get_gamelog_column_config(), width='stretch', hide_index=True)

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
                    display_df_local = display_df_local[cols_to_keep].copy()
                else:
                    display_df_local = display_df_local.copy()

                if 'WL' in display_df_local.columns:
                    display_df_local['WL'] = display_df_local['WL'].apply(
                        lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                    )

                col_cfg = get_gamelog_column_config()

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
                            
                            # Soft neon green highlight for dark theme
                            highlight.append('background-color: rgba(16, 185, 129, 0.22)' if row_highlight else '')
                        return pd.DataFrame([highlight]*len(s.columns)).T
                    
                    styled = display_df_local.style.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+7)', props=[('text-align', 'left')]), # Text columns left-aligned
                        dict(selector='th:nth-child(-n+7)', props=[('text-align', 'left')])
                    ]).apply(lambda _: highlight_rows(display_df_local), axis=None)
                    st.dataframe(styled, column_config=col_cfg, width='stretch', hide_index=True)
                except Exception as e:
                    st.dataframe(display_df_local, column_config=col_cfg, width='stretch', hide_index=True)

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
                agg_df['Hit %'] = agg_df['Hits'] / agg_df['GamesPlayed']
                agg_df['Record'] = agg_df.apply(lambda r: f"{r['Hits']} / {r['GamesPlayed']}", axis=1)
                agg_df['Streak'] = agg_df['ActiveStreak'].apply(
                    lambda s: f"🔥 {s} in a row" if s >= 3 else (f"{s} games" if s > 0 else "-")
                )
                
                display_cols = ['Player', 'Pos', 'Current Team', 'Age', 'YOS', 'Record', 'Hit %', 'Streak']
                display_df = agg_df[[c for c in display_cols if c in agg_df.columns]].copy()
                
                lb_column_config = {
                    "Player": st.column_config.TextColumn(
                        "Player",
                        help="⭐ 2026 Rookie | 🔥 Active Streak (3+)",
                        width="medium"
                    ),
                    "Pos": st.column_config.TextColumn("Pos", width="small"),
                    "Current Team": st.column_config.TextColumn("Team", width="small"),
                    "Age": st.column_config.TextColumn("Age", width="small"),
                    "YOS": st.column_config.TextColumn("Exp", help="Years of NBA Service (YOS)", width="small"),
                    "Record": st.column_config.TextColumn(
                        "Hits / GP",
                        help="Games Hit vs Total Games in timeframe",
                        width="small"
                    ),
                    "Hit %": st.column_config.ProgressColumn(
                        "Hit Rate",
                        help="Visual success rate across the selected timeframe",
                        format="%.0f%%",
                        min_value=0.0,
                        max_value=1.0,
                        width="medium"
                    ),
                    "Streak": st.column_config.TextColumn(
                        "Active Streak",
                        help="Current active consecutive hit streak",
                        width="small"
                    )
                }
                
                try:
                    def highlight_hot(val):
                        return 'background-color: rgba(249, 115, 22, 0.25)' if isinstance(val, str) and '🔥' in val else ''
                    
                    try:
                        styled_df = display_df.style.map(highlight_hot, subset=['Player'])
                    except AttributeError:
                        styled_df = display_df.style.applymap(highlight_hot, subset=['Player'])
                        
                    styled_df = styled_df.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+4)', props=[('text-align', 'left')]), # Text cols left-aligned
                        dict(selector='th:nth-child(-n+4)', props=[('text-align', 'left')])
                    ])
                        
                    event = st.dataframe(
                        styled_df,
                        column_config=lb_column_config,
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
                    st.dataframe(display_df, column_config=lb_column_config, width='stretch', hide_index=True)

            # Success Rate Dashboard Panel
            active_stats = [stat for stat in stat_fields if stat_inputs.get(stat, 0) > 0]
            if view_mode == 'Select Player' and selected_player:
                if active_stats:
                    with st.container(border=True):
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
                                return '<span style="color: #64748b;">-</span>'
                            if pct >= 70:
                                cls = "kpi-chip-green"
                            elif pct >= 50:
                                cls = "kpi-chip-amber"
                            else:
                                cls = "kpi-chip-red"
                            return f'<span class="kpi-chip {cls}">{pct:.1f}% <span style="opacity: 0.8; font-size: 11px; margin-left: 3px;">({hits}/{total})</span></span>'

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
                                    trend = f'<span style="color: #34d399; font-weight: 700;">🔥 Up (+{diff:.0f}%)</span>'
                                elif diff <= -10:
                                    trend = f'<span style="color: #f87171; font-weight: 700;">❄️ Down ({diff:.0f}%)</span>'
                                else:
                                    trend = '<span style="color: #94a3b8; font-weight: 500;">⚖️ Steady</span>'
                            else:
                                trend = '<span style="color: #64748b;">-</span>'

                            stat_name = primary_labels.get(stat) or secondary_labels.get(stat) or dict(combo_stats).get(stat) or stat
                            dashboard_rows.append(f"""
                            <tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.07);">
                                <td style="padding: 12px 14px; font-weight: 600; color: #f8fafc;">{stat_name} <span style="color: #38bdf8; font-weight: 700; margin-left: 4px;">({t_val}+)</span></td>
                                <td style="padding: 12px 14px; text-align: center;">{b5}</td>
                                <td style="padding: 12px 14px; text-align: center;">{b10}</td>
                                <td style="padding: 12px 14px; text-align: center;">{b20}</td>
                                <td style="padding: 12px 14px; text-align: center;">{bs}</td>
                                <td style="padding: 12px 14px; text-align: center;">{trend}</td>
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
                            <tr style="background: rgba(99, 102, 241, 0.16); font-weight: 700; border-top: 1px solid rgba(99, 102, 241, 0.4);">
                                <td style="padding: 12px 14px; color: #a5b4fc; font-weight: 800; letter-spacing: 0.02em;">🎯 ALL TARGETS (PARLAY HIT)</td>
                                <td style="padding: 12px 14px; text-align: center;">{cb5}</td>
                                <td style="padding: 12px 14px; text-align: center;">{cb10}</td>
                                <td style="padding: 12px 14px; text-align: center;">{cb20}</td>
                                <td style="padding: 12px 14px; text-align: center;">{cbs}</td>
                                <td style="padding: 12px 14px; text-align: center;">-</td>
                            </tr>
                            """)

                        dashboard_table = f"""
                        <div style="overflow-x: auto; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08); background: rgba(11, 15, 25, 0.5);">
                            <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                                <thead>
                                    <tr style="background: rgba(15, 23, 42, 0.85); border-bottom: 2px solid rgba(255, 255, 255, 0.1); text-align: left; color: #94a3b8;">
                                        <th style="padding: 10px 14px; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Target Stat Line</th>
                                        <th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 5 Games</th>
                                        <th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 10 Games</th>
                                        <th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 20 Games</th>
                                        <th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Full Season</th>
                                        <th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">L5 vs. Season Trend</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {''.join(dashboard_rows)}
                                </tbody>
                            </table>
                        </div>
                        """
                        st.markdown(dashboard_table, unsafe_allow_html=True)
            elif view_mode == 'Select Stat' and active_stats:
                with st.container(border=True):
                    st.markdown("### 🏆 Leaderboard Target Criteria")
                    criteria_chips = []
                    for s in active_stats:
                        lbl = primary_labels.get(s) or secondary_labels.get(s) or dict(combo_stats).get(s) or s
                        criteria_chips.append(f"<span style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); padding: 4px 10px; border-radius: 6px; font-weight: 600; color: #c7d2fe;'><b>{lbl}:</b> {stat_inputs[s]}+</span>")
                    st.markdown(f"Evaluating players against: {' &nbsp; '.join(criteria_chips)}", unsafe_allow_html=True)
                    st.caption("Use the tabs below to view top players across Last 5, Last 10, Last 20, or Full Season.")

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
