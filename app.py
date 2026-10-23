# Import Streamlit for web UI rendering and traceback for error diagnostics
import streamlit as st
import traceback

# Set page configuration to wide layout with custom page title
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
    background: rgba(15, 23, 42, 0.65);
    padding: 6px 8px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    gap: 8px;
}
div[data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 18px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    border: 1px solid transparent !important;
}
div[data-baseweb="tab"]:hover {
    color: #f1f5f9 !important;
    background: rgba(255, 255, 255, 0.04) !important;
}
div[data-baseweb="tab"][aria-selected="true"] {
    background: rgba(99, 102, 241, 0.2) !important;
    color: #ffffff !important;
    border: 1px solid rgba(99, 102, 241, 0.45) !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
}

/* Tactile Buttons with Active Press Physics */
div.stButton > button {
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background: rgba(30, 41, 59, 0.75) !important;
    color: #f1f5f9 !important;
    transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1) !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3) !important;
}
div.stButton > button:hover {
    background: rgba(99, 102, 241, 0.25) !important;
    border-color: rgba(99, 102, 241, 0.5) !important;
    color: #ffffff !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25) !important;
    transform: translateY(-1px);
}
div.stButton > button:active {
    transform: translateY(1px) scale(0.985) !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.4) !important;
}

/* Number Input Box Customization */
div[data-testid="stNumberInput"] {
    background: rgba(15, 23, 42, 0.5);
    border-radius: 10px;
    padding: 2px;
}
div[data-testid="stNumberInput"] input {
    font-family: 'Outfit', sans-serif !important;
    font-size: 16px !important;
    font-weight: 700 !important;
    color: #38bdf8 !important;
    text-align: center;
}

/* Metric Pill Badges */
.metric-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    color: #c7d2fe;
    box-shadow: 0 2px 8px rgba(99, 102, 241, 0.15);
}

/* Status Indicator Dot with Glow Pulse */
.live-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #10b981;
    box-shadow: 0 0 10px #10b981;
    animation: live-pulse 2s infinite ease-in-out;
}
@keyframes live-pulse {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* KPI Chips for Target Hit Rates */
.kpi-chip {
    padding: 4px 10px;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    display: inline-block;
    letter-spacing: 0.02em;
}
.kpi-chip-green {
    background: rgba(16, 185, 129, 0.18);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.15);
}
.kpi-chip-amber {
    background: rgba(245, 158, 11, 0.18);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
}
.kpi-chip-red {
    background: rgba(239, 68, 68, 0.18);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.4);
}

/* Wide Modal Dialog for Player Game Logs */
div[data-testid="stDialog"] div[role="dialog"] {
    width: 85vw !important;
    max-width: 1250px !important;
}
</style>
""", unsafe_allow_html=True)

# Safe imports for core data handling and database operations
try:
    import pandas as pd
    from datetime import datetime
    import os
    import sqlite3
# Handle missing required dependencies gracefully
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.stop()
# Catch startup exceptions with traceback display
except Exception as e:
    st.error(f"Startup Error: {e}")
    st.text(traceback.format_exc())
    st.stop()

# Authenticate users using Streamlit secrets password gate
def check_password():
    # Return true immediately if user already validated their credentials in session
    if st.session_state.get("password_correct", False):
        return True

    # Render clean login form for unauthenticated users
    with st.form("login_form"):
        st.write("### Login")
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
    
    # Process login credentials when submit button is pressed
    if submit:
        # Validate username and password against secrets configuration
        if "users" in st.secrets and user in st.secrets["users"] and st.secrets["users"][user] == pwd:
            st.session_state["password_correct"] = True
            st.rerun()
        # Mark login attempt as failed in session state
        else:
            st.session_state["password_correct"] = False

    # Display error banner if authentication failed
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 User not found or password incorrect")
        
    return False

# Main application execution wrapper guarded by password verification
try:
    if check_password():
        DB_PATH = "gamelogs.db"

        # Check last modification timestamp of a file to invalidate caches when data updates
        def file_mtime(path):
            return os.path.getmtime(path) if os.path.exists(path) else 0

        # Load game logs from SQLite database with automated cache invalidation on file update
        @st.cache_data
        def load_gamelogs(db_path, mtime):
            # Return empty DataFrame if SQLite database file does not exist
            if not os.path.exists(db_path):
                return pd.DataFrame()
            # Read game logs table from SQLite database
            try:
                conn = sqlite3.connect(db_path)
                df = pd.read_sql_query("SELECT * FROM gamelogs", conn)
                conn.close()
                # Compute helper columns for season labeling and preseason categorization
                if not df.empty:
                    df['season_label'] = df['Season']
                    df['is_preseason'] = df['GameType'] == 'Preseason'
                return df
            # Catch database query errors
            except Exception as e:
                st.error(f"Error reading database: {e}")
                return pd.DataFrame()

        # Load player roster table from CSV or Excel with automated cache invalidation
        @st.cache_data
        def load_players_data(path, mtime):
            # Return empty DataFrame if roster file does not exist
            if not os.path.exists(path):
                return pd.DataFrame()
            # Read players roster data from CSV or Excel
            try:
                if path.endswith(".csv"):
                    return pd.read_csv(path)
                return pd.read_excel(path)
            # Catch file read errors
            except Exception as e:
                st.error(f"Error reading {path}: {e}")
                return pd.DataFrame()

        # Resolve available roster file path
        PLAYERS_PATH = "players.csv" if os.path.exists("players.csv") else "players.xlsx"

        # Load data using modification timestamps as cache keys
        df = load_gamelogs(DB_PATH, file_mtime(DB_PATH))
        players_df = load_players_data(PLAYERS_PATH, file_mtime(PLAYERS_PATH))

        # Show warning if database is missing or empty
        if df.empty:
            st.warning("No data found in gamelogs.db or database file is missing.")
        # Render main application when data is available
        else:
            all_players = sorted(df['Player'].unique())

            # Render sleek sidebar branding and navigation header
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

            # View Mode selector (Player Logs vs Prop Leaderboard)
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
                # Helper function to format 2026-27 season display string
                def format_season_display(s: str) -> str:
                    if not isinstance(s, str):
                        return ""
                    m = re.match(r"^(\d{4})-(\d{2})$", s.strip())
                    if m:
                        y1, y2 = m.groups()
                        full_label = f"{y1}-20{y2}"
                        # Highlight current active season in dropdown
                        if s == "2026-27":
                            return f"{full_label} (Current Season)"
                        return full_label
                    return s

                # Extract and sort unique seasons in reverse chronological order
                raw_seasons = sorted(df['season_label'].dropna().unique(), reverse=True)
                season_display_map = {format_season_display(s): s for s in raw_seasons}
                display_options = list(season_display_map.keys())

                # Default to selecting the most recent season
                default_display = [display_options[0]] if display_options else []
                selected_display_seasons = st.multiselect(
                    'Select Season(s)',
                    display_options,
                    default=default_display
                )
                selected_seasons = [season_display_map[d] for d in selected_display_seasons if d in season_display_map]
                
                # Multi-select filter for NBA game categories
                all_game_types = ['Regular Season', 'Playoffs', 'Play-In', 'Preseason']
                selected_game_types = st.multiselect(
                    'Select Game Type(s)',
                    all_game_types,
                    default=['Regular Season', 'Playoffs', 'Preseason']
                )

            # Identify rookie players from roster data where Years of Service is 0 or 'R'
            rookie_names = set()
            if not players_df.empty and 'YOS' in players_df.columns:
                rookie_mask = (players_df['YOS'].astype(str).str.strip() == '0') | (players_df['YOS'].astype(str).str.upper().str.strip() == 'R')
                rookie_names = set(players_df[rookie_mask]['Player'].dropna().unique())

            # Build full universe of unique players across both database and roster
            db_players = set(df['Player'].dropna().unique())
            csv_players = set(players_df['Player'].dropna().unique()) if not players_df.empty else set()
            all_known_players = sorted(list(db_players.union(csv_players)))

            # Player Universe filter (All, Rookies, or Veterans)
            st.sidebar.write("")
            st.sidebar.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>👥 Player Universe</span>", unsafe_allow_html=True)
            player_pool = st.sidebar.radio(
                'Filter by Class',
                ['All Players', '⭐ 2026 Rookie Class', 'Veterans Only'],
                index=0,
                key='player_pool_select',
                label_visibility='collapsed'
            )

            # Filter selectable player list based on the chosen universe pool
            if player_pool == '⭐ 2026 Rookie Class':
                available_players = [p for p in all_known_players if p in rookie_names]
            elif player_pool == 'Veterans Only':
                available_players = [p for p in all_known_players if p not in rookie_names]
            else:
                available_players = all_known_players

            # Selectbox dropdown to pick active player when in Player Logs mode
            selected_player = None
            if view_mode == 'Select Player':
                st.sidebar.write("")
                st.sidebar.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>🔍 Select Player</span>", unsafe_allow_html=True)
                # Show warning if current pool has no available players
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

            # Sidebar database telemetry widget showing games, roster count, and tracked rookies
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

            # Filter game logs based on selected seasons and game categories
            df_filtered = df.copy()
            if selected_seasons:
                df_filtered = df_filtered[df_filtered['season_label'].isin(selected_seasons)]
            if selected_game_types:
                df_filtered = df_filtered[df_filtered['GameType'].isin(selected_game_types)]

            # Filter Leaderboard dataset based on player universe class selection
            if view_mode == 'Select Stat':
                if player_pool == '⭐ 2026 Rookie Class':
                    df_filtered = df_filtered[df_filtered['Player'].isin(rookie_names)]
                elif player_pool == 'Veterans Only':
                    df_filtered = df_filtered[~df_filtered['Player'].isin(rookie_names)]

            # Filter dataset to selected player in Player Logs mode
            if view_mode == 'Select Player' and selected_player:
                df_filtered = df_filtered[df_filtered['Player'] == selected_player]

            # Main canvas brand header with animated live database indicator
            st.markdown("""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; border-bottom: 1px solid rgba(255, 255, 255, 0.08); padding-bottom: 1rem;">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 32px;">🏀</span>
                        <span style="font-family: 'Outfit', sans-serif; font-size: 28px; font-weight: 900; letter-spacing: -0.03em; background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 50%, #94a3b8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">PropPulse NBA</span>
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
            
            # Display player header or leaderboard title depending on active view mode
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
                st.caption("Top 25 players ranked by hit rate and consistency across Last 5, 10, 20, or Full Season games.")

            # Define ordered table display columns and target stat fields
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

                # Milestone values for quick ladder chips
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

                # Callback handlers for preset and ladder buttons (runs BEFORE widgets instantiate)
                def set_stat_target(stat_name, target_value):
                    st.session_state[f'stat_{stat_name}'] = target_value

                # Callback to set multiple target values simultaneously for combination presets
                def set_multi_targets(**targets):
                    for stat_name, target_value in targets.items():
                        st.session_state[f'stat_{stat_name}'] = target_value

                # Callback to reset all stat input targets back to 0
                def clear_all_targets():
                    for s in stat_fields:
                        st.session_state[f'stat_{s}'] = 0

                # Quick Prop Presets Row
                preset_bar, clear_bar = st.columns([6, 1])
                with preset_bar:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>⚡ Popular Betting Presets:</span>", unsafe_allow_html=True)
                    p_cols = st.columns(7)
                    # 1-click popular betting preset buttons with on_click callbacks
                    p_cols[0].button("🏀 20+ PTS", use_container_width=True, help="Set Points to 20+", on_click=set_stat_target, args=('PTS', 20))
                    p_cols[1].button("🏀 25+ PTS", use_container_width=True, help="Set Points to 25+", on_click=set_stat_target, args=('PTS', 25))
                    p_cols[2].button("🎯 3+ 3PM", use_container_width=True, help="Set 3-Pointers to 3+", on_click=set_stat_target, args=('TPM', 3))
                    p_cols[3].button("💪 8+ REB", use_container_width=True, help="Set Rebounds to 8+", on_click=set_stat_target, args=('REB', 8))
                    p_cols[4].button("🤝 6+ AST", use_container_width=True, help="Set Assists to 6+", on_click=set_stat_target, args=('AST', 6))
                    p_cols[5].button("🔥 30+ PRA", use_container_width=True, help="Set PTS + REB + AST to 30+", on_click=set_stat_target, args=('P|R|A', 30))
                    p_cols[6].button("⭐ 10P/10R DD", use_container_width=True, help="Double-Double line: 10+ PTS & 10+ REB", on_click=set_multi_targets, kwargs={'PTS': 10, 'REB': 10})
                with clear_bar:
                    st.markdown("<span style='font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em;'>Reset:</span>", unsafe_allow_html=True)
                    # Reset button to clear all active target filters
                    st.button('🧹 Clear All', use_container_width=True, help="Reset all stat lines", on_click=clear_all_targets)

                st.write("")

                # Row 1: Primary Metrics (PTS, 3PM, REB, AST, STL)
                row1 = st.columns(5)
                primary_stats = ['PTS', 'TPM', 'REB', 'AST', 'STL']
                primary_labels = {
                    'PTS': '🏀 Points',
                    'TPM': '🎯 3-Pointers',
                    'REB': '💪 Rebounds',
                    'AST': '🤝 Assists',
                    'STL': '⚡ Steals'
                }
                # Render number inputs and milestone ladder chips for primary metrics
                for i, stat in enumerate(primary_stats):
                    with row1[i]:
                        val = st.number_input(primary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        # Render milestone ladder chips underneath each input
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                l_cols[idx].button(
                                    f"{l_val}+",
                                    key=f"ladder_{stat}_{l_val}",
                                    use_container_width=True,
                                    on_click=set_stat_target,
                                    args=(stat, l_val)
                                )

                st.write("")

                # Row 2: Defensive & Combination Metrics (BLK, TOV, PRA, PA, PR)
                row2 = st.columns(5)
                secondary_stats = ['BLK', 'TOV']
                secondary_labels = {
                    'BLK': '🛡️ Blocks',
                    'TOV': '⚠️ Turnovers'
                }
                # Render number inputs and ladder chips for defensive metrics
                for i, stat in enumerate(secondary_stats):
                    with row2[i]:
                        val = st.number_input(secondary_labels[stat], min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        # Render ladder chips for defensive stats
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                l_cols[idx].button(
                                    f"{l_val}+",
                                    key=f"ladder_{stat}_{l_val}",
                                    use_container_width=True,
                                    on_click=set_stat_target,
                                    args=(stat, l_val)
                                )

                # Combo metrics mapping
                combo_stats = [
                    ('P|R|A', '🔥 PTS + REB + AST'),
                    ('P|A', '🔥 PTS + AST'),
                    ('P|R', '🔥 PTS + REB')
                ]
                # Render number inputs and ladder chips for combo stats
                for i, (stat, label) in enumerate(combo_stats):
                    with row2[i + 2]:
                        val = st.number_input(label, min_value=0, step=1, key=f'stat_{stat}', placeholder="0")
                        stat_inputs[stat] = val if val is not None else 0
                        # Render ladder chips for combo stats
                        if stat in stat_ladders:
                            l_cols = st.columns(len(stat_ladders[stat]))
                            for idx, l_val in enumerate(stat_ladders[stat]):
                                l_cols[idx].button(
                                    f"{l_val}+",
                                    key=f"ladder_{stat}_{l_val}",
                                    use_container_width=True,
                                    on_click=set_stat_target,
                                    args=(stat, l_val)
                                )

            # Build Streamlit column configuration dictionary for game log tables
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
                # Add customized number formatting and tooltip targets for each stat column
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
                # Modern Streamlit dialog decorator available in 1.35+
                @st.dialog("Player Game Logs", width="large")
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.write(f"Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Opponent', 'WL', 'MIN', 'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    # Standardize game date string format
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    # Map win/loss indicators to green/red status badges
                    if 'WL' in df_out.columns:
                        df_out['WL'] = df_out['WL'].apply(
                            lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                        )
                    st.dataframe(df_out, column_config=get_gamelog_column_config(), width='stretch', hide_index=True)
            # Fallback dialog implementation for older Streamlit versions without st.dialog
            except AttributeError:
                def show_player_logs_dialog(player_name, df_player_logs, timeframe):
                    st.markdown(f"### Detailed **{timeframe}** logs for **{player_name}**:")
                    dialog_cols = ['Date', 'Opponent', 'WL', 'MIN', 'PTS', 'TPM', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'P|R|A', 'P|A', 'P|R']
                    df_out = df_player_logs[[c for c in dialog_cols if c in df_player_logs.columns]].copy()
                    # Standardize game date string format
                    if 'Date' in df_out.columns:
                        try:
                            df_out['Date'] = pd.to_datetime(df_out['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                        except:
                            pass
                    # Map win/loss indicators to green/red status badges
                    if 'WL' in df_out.columns:
                        df_out['WL'] = df_out['WL'].apply(
                            lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                        )
                    st.dataframe(df_out, column_config=get_gamelog_column_config(), width='stretch', hide_index=True)

            # Build sorted display DataFrame sliced to n most recent games
            def make_display_df(df_source, n=None):
                # Return empty schema if source data is empty
                if df_source.empty:
                    return pd.DataFrame(columns=columns_to_display)
                # Slice to n most recent games sorted by date descending
                if n is not None:
                    temp = df_source.sort_values('Date', ascending=False).head(n).copy()
                # Sort all games by date descending if no slice limit is provided
                else:
                    temp = df_source.sort_values('Date', ascending=False).copy()
                
                # Compute combination stat totals (PRA, PA, PR) if component stats are present
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].astype(float).sum(axis=1)
                
                # Standardize date format to YYYY-MM-DD
                if 'Date' in temp.columns:
                    temp['Date'] = pd.to_datetime(temp['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
                
                # Format percentage metrics to 3 decimal places
                for col in ['FGPercent', 'TPPercent', 'FTPercent', 'FIC']:
                    if col in temp.columns:
                        temp[col] = temp[col].apply(lambda x: f'{x:.3f}' if pd.notnull(x) else '')
                
                # Ensure all display columns exist in output
                for col in columns_to_display:
                    if col not in temp.columns:
                        temp[col] = ''
                        
                return temp[columns_to_display].copy()

            # Generate game log DataFrames for each time horizon (Last 5, 10, 20, and Full Season)
            display_5 = make_display_df(df_filtered, 5)
            display_10 = make_display_df(df_filtered, 10)
            display_20 = make_display_df(df_filtered, 20)
            display_season = make_display_df(df_filtered, None)

            # Compute percentage of games where player hit each target stat
            def compute_percent_hits(display_df_local):
                results = {}
                n = len(display_df_local)
                # Return null values if no games exist in this timeframe
                if n == 0:
                    for stat in stat_fields:
                        results[stat] = None
                    return results
                # Calculate hit rate percentage for each active stat filter
                for stat in stat_fields:
                    if stat in display_df_local.columns and stat_inputs[stat] > 0:
                        mask = pd.to_numeric(display_df_local[stat], errors='coerce') >= stat_inputs[stat]
                        percent = mask.sum() / n * 100
                        results[stat] = percent
                    else:
                        results[stat] = None
                return results

            # Render player game logs table with hit rate badges and soft green row highlighting
            def render_table_with_summary(display_df_local, title):
                # Inform user if no game logs exist for the current filter scope
                if display_df_local.empty:
                    st.info(f"No game logs recorded for {title} in the selected season(s) and game type(s).")
                    return

                # Calculate success rates across active stat targets
                percents = compute_percent_hits(display_df_local)
                
                # Filter down to actively targeted stats
                active_stats = [stat for stat in stat_fields if stat_inputs.get(stat, 0) > 0]
                # Render metric badges if target filters are active
                if active_stats:
                    percent_cols = st.columns(len(active_stats))
                    for i, stat in enumerate(active_stats):
                        percent_str = f"{percents[stat]:.1f}%" if percents[stat] is not None else "-"
                        percent_cols[i].markdown(
                            f'<div class="metric-badge"><b>{stat}:</b> {percent_str}</div>',
                            unsafe_allow_html=True
                        )
                        
                    # Filter table columns to base identifiers plus active stat targets
                    base_cols = ['Date', 'Team', 'Opponent', 'WL', 'Status', 'Pos', 'MIN']
                    cols_to_keep = [c for c in base_cols + active_stats if c in display_df_local.columns]
                    display_df_local = display_df_local[cols_to_keep].copy()
                else:
                    display_df_local = display_df_local.copy()

                # Format Win/Loss indicators with visual colored badges
                if 'WL' in display_df_local.columns:
                    display_df_local['WL'] = display_df_local['WL'].apply(
                        lambda x: '🟢 W' if str(x).strip().upper().startswith('W') else ('🔴 L' if str(x).strip().upper().startswith('L') else str(x))
                    )

                col_cfg = get_gamelog_column_config()

                # Apply vectorized soft neon green background styling to matching game rows
                try:
                    def highlight_rows(s):
                        mask = pd.Series([True] * len(s), index=s.index)
                        has_filter = False
                        # Evaluate all active target stat lines across table rows
                        for stat in stat_fields:
                            if stat_inputs.get(stat, 0) > 0 and stat in s.columns:
                                has_filter = True
                                mask = mask & (pd.to_numeric(s[stat], errors='coerce') >= stat_inputs[stat])
                        
                        # Generate CSS styling matrix matching the DataFrame index and columns
                        css_df = pd.DataFrame('', index=s.index, columns=s.columns)
                        # Highlight rows where all target filters were achieved
                        if has_filter:
                            css_df.loc[mask, :] = 'background-color: rgba(16, 185, 129, 0.22)'
                        return css_df
                    
                    # Apply text alignment and custom row styling
                    styled = display_df_local.style.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+7)', props=[('text-align', 'left')]), # Text columns left-aligned
                        dict(selector='th:nth-child(-n+7)', props=[('text-align', 'left')])
                    ]).apply(lambda _: highlight_rows(display_df_local), axis=None)
                    st.dataframe(styled, column_config=col_cfg, width='stretch', hide_index=True)
                # Fall back to unstyled dataframe if styling fails
                except Exception as e:
                    st.dataframe(display_df_local, column_config=col_cfg, width='stretch', hide_index=True)

            # Render Prop Leaderboard aggregating top players hitting target stats in the selected timeframe
            def render_stat_summary(df_all, players_base_df, n_games, title):
                has_active_filters = any(stat_inputs[s] > 0 for s in stat_fields)
                # Prompt user to input target stats if none are currently set
                if not has_active_filters:
                    st.info("Input a stat filter above to see top players.")
                    return
                
                # Check for empty game logs dataset
                if df_all.empty:
                    st.write("No gamelogs available.")
                    return
                
                # Calculate combo stat totals for leaderboard ranking
                temp = df_all.copy()
                for combo, parts in [('P|R|A', ['PTS', 'REB', 'AST']), ('P|A', ['PTS', 'AST']), ('P|R', ['PTS', 'REB'])]:
                    if all(p in temp.columns for p in parts):
                        temp[combo] = temp[parts].apply(pd.to_numeric, errors='coerce').sum(axis=1)

                # Keep player, date, and active stat columns
                cols_to_keep = ['Player', 'Date'] + [col for col in stat_fields if stat_inputs[col] > 0]
                temp_filtered = temp[[c for c in cols_to_keep if c in temp.columns]].copy()
                
                # Sort games by player and date descending, slicing to n recent games per player
                temp_filtered['Date'] = pd.to_datetime(temp_filtered['Date'], errors='coerce')
                temp_filtered = temp_filtered.sort_values(['Player', 'Date'], ascending=[True, False])
                if n_games is not None:
                    temp_filtered = temp_filtered.groupby('Player').head(n_games)
                
                # Determine hit status across all active target filters for each game
                hit_mask = pd.Series([True] * len(temp_filtered), index=temp_filtered.index)
                for stat in stat_fields:
                    if stat_inputs[stat] > 0 and stat in temp_filtered.columns:
                        hit_mask = hit_mask & (pd.to_numeric(temp_filtered[stat], errors='coerce') >= stat_inputs[stat])
                
                temp_filtered['Hit'] = hit_mask.astype(int)
                
                # Calculate current active consecutive hit streak for each player
                def calc_active_streak(series):
                    streak = 0
                    for val in series:
                        if val == 1:
                            streak += 1
                        else:
                            break
                    return streak

                # Group by player to compute total hits, games played, and active streaks
                agg_df = temp_filtered.groupby('Player').agg(
                    Hits=('Hit', 'sum'),
                    GamesPlayed=('Hit', 'count'),
                    ActiveStreak=('Hit', calc_active_streak)
                ).reset_index()
                
                # Keep only players with at least 1 hit
                agg_df = agg_df[agg_df['Hits'] > 0]
                
                # Display message if no players achieved the targets
                if agg_df.empty:
                    st.write("No players found hitting these stats in the selected timeframe.")
                    return
                
                # Merge player metadata (position, team) from roster table
                if not players_base_df.empty:
                    agg_df = agg_df.merge(players_base_df[['Player', 'Pos', 'Current Team']], on='Player', how='left')
                else:
                    for col in ['Pos', 'Current Team']:
                        agg_df[col] = ''
                
                # Mark players with active streaks of 3 or more games as hot
                agg_df['IsHotStreak'] = agg_df['ActiveStreak'] >= 3
                agg_df['LastName'] = agg_df['Player'].apply(lambda n: n.split(' ')[-1] if isinstance(n, str) and ' ' in n else n)
                # Sort leaderboard by hot streak, total hits, and last name
                agg_df = agg_df.sort_values(['IsHotStreak', 'Hits', 'LastName'], ascending=[False, False, True]).head(25)
                
                # Format player display label with flame emoji for hot streaks and star for rookies
                def format_lb_player(r):
                    base = r['Player']
                    prefix = "🔥 " if r['IsHotStreak'] else ""
                    if base in rookie_names:
                        prefix += "⭐ "
                    return f"{prefix}{base}"

                # Calculate hit rate percentage and formatted record strings
                agg_df['Player'] = agg_df.apply(format_lb_player, axis=1)
                agg_df['Hit %'] = agg_df['Hits'] / agg_df['GamesPlayed']
                agg_df['Record'] = agg_df.apply(lambda r: f"{r['Hits']} / {r['GamesPlayed']}", axis=1)
                agg_df['Streak'] = agg_df['ActiveStreak'].apply(
                    lambda s: f"🔥 {s} in a row" if s >= 3 else (f"{s} games" if s > 0 else "-")
                )
                
                display_cols = ['Player', 'Pos', 'Current Team', 'Record', 'Hit %', 'Streak']
                display_df = agg_df[[c for c in display_cols if c in agg_df.columns]].copy()
                
                # Configure Leaderboard columns with visual progress bar for Hit Rate
                lb_column_config = {
                    "Player": st.column_config.TextColumn(
                        "Player",
                        help="⭐ 2026 Rookie | 🔥 Active Streak (3+)",
                        width="medium"
                    ),
                    "Pos": st.column_config.TextColumn("Pos", width="small"),
                    "Current Team": st.column_config.TextColumn("Team", width="small"),
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
                
                # Render interactive leaderboard dataframe with row selection to trigger player dialog
                try:
                    # Highlight hot streak player rows with subtle orange tint
                    def highlight_hot(val):
                        return 'background-color: rgba(249, 115, 22, 0.25)' if isinstance(val, str) and '🔥' in val else ''
                    
                    # Apply styling across pandas versions
                    try:
                        styled_df = display_df.style.map(highlight_hot, subset=['Player'])
                    except AttributeError:
                        styled_df = display_df.style.applymap(highlight_hot, subset=['Player'])
                        
                    styled_df = styled_df.set_properties(**{'text-align': 'right'}).set_table_styles([
                        dict(selector='th', props=[('text-align', 'right')]),
                        dict(selector='td:nth-child(-n+3)', props=[('text-align', 'left')]), # Text cols left-aligned
                        dict(selector='th:nth-child(-n+3)', props=[('text-align', 'left')])
                    ])
                        
                    # Render interactive leaderboard table with click-to-view logs
                    event = st.dataframe(
                        styled_df,
                        column_config=lb_column_config,
                        width='stretch',
                        hide_index=True,
                        on_select="rerun",
                        selection_mode="single-row"
                    )
                    
                    # Open game logs dialog popup when user clicks on a player row
                    if event and hasattr(event, 'selection') and hasattr(event.selection, 'rows') and len(event.selection.rows) > 0:
                        row_idx = event.selection.rows[0]
                        clean_name = display_df.iloc[row_idx]['Player'].replace('🔥 ', '').replace('⭐ ', '').strip()
                        
                        player_details = temp[temp['Player'] == clean_name].copy()
                        player_details['Date'] = pd.to_datetime(player_details['Date'], errors='coerce')
                        # Slice to selected game count if limited
                        if n_games is not None:
                            player_details = player_details.sort_values('Date', ascending=False).head(n_games)
                        else:
                            player_details = player_details.sort_values('Date', ascending=False)
                        show_player_logs_dialog(clean_name, player_details, title)

                # Fallback to standard dataframe if advanced styling fails
                except Exception as e:
                    st.dataframe(display_df, column_config=lb_column_config, width='stretch', hide_index=True)

            # Success Rate Dashboard Panel evaluating active prop targets across multiple horizons
            active_stats = [stat for stat in stat_fields if stat_inputs.get(stat, 0) > 0]
            if view_mode == 'Select Player' and selected_player:
                # Render dashboard card if target stats are active
                if active_stats:
                    with st.container(border=True):
                        st.markdown("### 🎯 Target Success Rate Dashboard")
                        st.caption(f"Cross-referencing recent form (L5, L10, L20) against full season baseline for **{selected_player}**.")

                        # Calculate hit rate percentage and game hit counts for a given horizon
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

                        # Format color-coded KPI badge based on hit rate percentage
                        def format_kpi_badge(pct, hits, total):
                            if pct is None or total == 0:
                                return '<span style="color: #64748b;">-</span>'
                            # Green badge for hit rates >= 70%
                            if pct >= 70:
                                cls = "kpi-chip-green"
                            # Amber badge for hit rates between 50% and 69%
                            elif pct >= 50:
                                cls = "kpi-chip-amber"
                            # Red badge for hit rates < 50%
                            else:
                                cls = "kpi-chip-red"
                            return f'<span class="kpi-chip {cls}">{pct:.1f}% <span style="opacity: 0.8; font-size: 11px; margin-left: 3px;">({hits}/{total})</span></span>'

                        dashboard_rows = []
                        # Evaluate hit rates and form trends for each active stat target
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

                            # Calculate trend comparing Last 5 games against Full Season baseline
                            if p5 is not None and ps is not None and tot5 > 0 and tots > 0:
                                diff = p5 - ps
                                # Trending up if L5 hit rate is 10%+ higher than season baseline
                                if diff >= 10:
                                    trend = f'<span style="color: #34d399; font-weight: 700;">🔥 Up (+{diff:.0f}%)</span>'
                                # Trending down if L5 hit rate is 10%+ lower than season baseline
                                elif diff <= -10:
                                    trend = f'<span style="color: #f87171; font-weight: 700;">❄️ Down ({diff:.0f}%)</span>'
                                # Steady performance if within +/- 10%
                                else:
                                    trend = '<span style="color: #94a3b8; font-weight: 500;">⚖️ Steady</span>'
                            else:
                                trend = '<span style="color: #64748b;">-</span>'

                            stat_name = primary_labels.get(stat) or secondary_labels.get(stat) or dict(combo_stats).get(stat) or stat
                            # Construct individual table row HTML
                            dashboard_rows.append(
                                f'<tr style="border-bottom: 1px solid rgba(255, 255, 255, 0.07);">'
                                f'<td style="padding: 12px 14px; font-weight: 600; color: #f8fafc;">{stat_name} <span style="color: #38bdf8; font-weight: 700; margin-left: 4px;">({t_val}+)</span></td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{b5}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{b10}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{b20}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{bs}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{trend}</td>'
                                f'</tr>'
                            )

                        # Calculate combination parlay hit rate when 2 or more targets are active
                        if len(active_stats) >= 2:
                            def calc_parlay(df_sub):
                                if df_sub.empty:
                                    return None, 0, 0
                                mask = pd.Series([True] * len(df_sub), index=df_sub.index)
                                # Evaluate intersection across all active target filters
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

                            # Append parlay combo summary row
                            dashboard_rows.append(
                                f'<tr style="background: rgba(99, 102, 241, 0.16); font-weight: 700; border-top: 1px solid rgba(99, 102, 241, 0.4);">'
                                f'<td style="padding: 12px 14px; color: #a5b4fc; font-weight: 800; letter-spacing: 0.02em;">🎯 ALL TARGETS (PARLAY HIT)</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{cb5}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{cb10}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{cb20}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">{cbs}</td>'
                                f'<td style="padding: 12px 14px; text-align: center;">-</td>'
                                f'</tr>'
                            )

                        rows_html = "".join(dashboard_rows)
                        # Build complete dashboard table HTML string
                        dashboard_table = (
                            f'<div style="overflow-x: auto; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.08); background: rgba(11, 15, 25, 0.5);">'
                            f'<table style="width: 100%; border-collapse: collapse; font-size: 14px;">'
                            f'<thead>'
                            f'<tr style="background: rgba(15, 23, 42, 0.85); border-bottom: 2px solid rgba(255, 255, 255, 0.1); text-align: left; color: #94a3b8;">'
                            f'<th style="padding: 10px 14px; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Target Stat Line</th>'
                            f'<th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 5 Games</th>'
                            f'<th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 10 Games</th>'
                            f'<th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Last 20 Games</th>'
                            f'<th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">Full Season</th>'
                            f'<th style="padding: 10px 14px; text-align: center; font-weight: 600; text-transform: uppercase; font-size: 12px; letter-spacing: 0.05em;">L5 vs. Season Trend</th>'
                            f'</tr>'
                            f'</thead>'
                            f'<tbody>{rows_html}</tbody>'
                            f'</table>'
                            f'</div>'
                        )
                        # Render pure HTML via st.html bypassing Markdown code block parser
                        if hasattr(st, "html"):
                            st.html(dashboard_table)
                        else:
                            st.markdown(dashboard_table, unsafe_allow_html=True)
            # Display target criteria badges in Leaderboard mode
            elif view_mode == 'Select Stat' and active_stats:
                with st.container(border=True):
                    st.markdown("### 🏆 Leaderboard Target Criteria")
                    criteria_chips = []
                    # Format chips for each active target
                    for s in active_stats:
                        lbl = primary_labels.get(s) or secondary_labels.get(s) or dict(combo_stats).get(s) or s
                        criteria_chips.append(f"<span style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); padding: 4px 10px; border-radius: 6px; font-weight: 600; color: #c7d2fe;'><b>{lbl}:</b> {stat_inputs[s]}+</span>")
                    st.markdown(f"Evaluating players against: {' &nbsp; '.join(criteria_chips)}", unsafe_allow_html=True)
                    st.caption("Use the tabs below to view top players across Last 5, Last 10, Last 20, or Full Season.")

            # Tabbed Interface across 4 Horizons (Last 5, 10, 20, and Full Season)
            st.markdown('---')
            tab5, tab10, tab20, tab_season = st.tabs([
                "📊 Last 5 Games",
                "📈 Last 10 Games",
                "🏆 Last 20 Games",
                "📅 Full Season"
            ])
            
            # Tab 1: Last 5 Games
            with tab5:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_5, 'Last 5 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 5, 'Last 5 Games')
                    
            # Tab 2: Last 10 Games
            with tab10:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_10, 'Last 10 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 10, 'Last 10 Games')
                    
            # Tab 3: Last 20 Games
            with tab20:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_20, 'Last 20 Games')
                else:
                    render_stat_summary(df_filtered, players_df, 20, 'Last 20 Games')

            # Tab 4: Full Season Baseline
            with tab_season:
                if view_mode == 'Select Player':
                    render_table_with_summary(display_season, 'Full Season')
                else:
                    render_stat_summary(df_filtered, players_df, None, 'Full Season')

# Global error catch displaying informative exception details
except Exception as e:
    st.error(f"An error occurred while running the app: {e}")
    st.text(traceback.format_exc())
