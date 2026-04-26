import streamlit as st
import pandas as pd

df = pd.DataFrame({'Player': ['A', 'B', 'C'], 'Hits': [1, 2, 3]})
st.write("Test Dataframe")
event = st.dataframe(df, on_select="rerun", selection_mode="single-row")
st.write(event)
