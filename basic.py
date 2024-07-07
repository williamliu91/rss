import streamlit as st
import pandas as pd
import numpy as np

st.title("My Streamlit App")

# Create some sample data
data = pd.DataFrame(
    np.random.randn(10, 2),
    columns=['Column 1', 'Column 2']
)

# Display the data as a table
st.write(data)

# Display a line chart
st.line_chart(data)

# Add a slider
x = st.slider('Select a value')
st.write('Selected value:', x)

# Add a selectbox
option = st.selectbox('Which column to display?', data.columns)
st.write('You selected:', option)
st.line_chart(data[[option]])

