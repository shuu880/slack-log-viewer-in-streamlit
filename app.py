import streamlit as st
import os
import json
import pandas as pd
from datetime import datetime
import re
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(layout="wide", page_title='Slack Channel Data Viewer')

# Application title
st.title('Slack Log Viewer')

st.image("images/logo.png", width=300)

# Path to the dumps folder
DUMPS_PATH = 'dumps'

@st.cache_data
def get_available_channels():
    channels = set()
    for year_dir in os.listdir(DUMPS_PATH):
        if year_dir.startswith('from_'):
            year_path = os.path.join(DUMPS_PATH, year_dir)
            channels.update([f.split('_')[0] for f in os.listdir(year_path) if f.endswith('.json')])
    return sorted(list(channels))

# Channel selection
selected_channel = st.selectbox('Select a channel', get_available_channels())

# Display order selection
sort_order = st.selectbox("Display order", ("Newest first", "Oldest first"))

# Function to exclude "joined the channel" messages
def filter_join_messages(message):
    return not re.match(r'<@U\w+> has joined the channel', message.get('text', ''))

@st.cache_data
def load_channel_data(channel):
    all_data = []
    for year_dir in os.listdir(DUMPS_PATH):
        if year_dir.startswith('from_'):
            year_path = os.path.join(DUMPS_PATH, year_dir)
            json_file = next((f for f in os.listdir(year_path) if f.startswith(f"{channel}_")), None)
            if json_file:
                json_path = os.path.join(year_path, json_file)
                with open(json_path, 'r') as f:
                    data = json.load(f)
                if data['messages']:
                    all_data.extend(data['messages'])
    return all_data

def display_thread(thread_messages):
    for msg in thread_messages:
        ts = msg['ts']
        formatted_ts = pd.to_datetime(float(ts), unit='s') if not isinstance(ts, pd.Timestamp) else ts
        st.text(f"{msg['user']} - {formatted_ts}")
        st.markdown(msg['text'])
        st.markdown("---")

def create_basic_statistics_figure(num_messages, num_unique_users, start_date, end_date):
    fig = go.Figure()
    fig.add_trace(go.Bar(x=['Number of Messages'], y=[num_messages], name='Messages', marker_color='blue'))
    fig.add_trace(go.Bar(x=['Number of Unique Users'], y=[num_unique_users], name='Unique Users', marker_color='orange'))
    fig.add_annotation(x=0.5, y=max(num_messages, num_unique_users) * 1.1,
                       text=f'Period: {start_date} to {end_date}',
                       showarrow=False, font=dict(size=14))
    fig.update_layout(title='Basic Statistics',
                      barmode='group',
                      xaxis_title='Statistics',
                      yaxis_title='Count',
                      showlegend=True)
    return fig

def main():
    if selected_channel:
        messages = load_channel_data(selected_channel)
        
        if not messages:
            st.warning(f"No messages found in the {selected_channel} channel.")
            return

        filtered_messages = list(filter(filter_join_messages, messages))
        df = pd.DataFrame(filtered_messages)
        
        if 'ts' not in df.columns:
            st.error("Error: 'ts' column not found in the data. Please check the structure of your JSON file.")
            st.write("Available columns:", df.columns)
            return

        df['ts'] = pd.to_datetime(df['ts'], unit='s')
        if 'thread_ts' in df.columns:
            df['thread_ts'] = pd.to_datetime(df['thread_ts'], unit='s')
        
        # Date range selection feature
        st.subheader('Select Date Range')
        min_date = df['ts'].min().date()
        max_date = df['ts'].max().date()
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input('Start Date', min_date, min_value=min_date, max_value=max_date)
        with col2:
            end_date = st.date_input('End Date', max_date, min_value=min_date, max_value=max_date)
        
        # Filter data based on selected date range
        mask = (df['ts'].dt.date >= start_date) & (df['ts'].dt.date <= end_date)
        df = df.loc[mask]

        # Text search feature
        search_query = st.text_input("Search messages (case-insensitive):")
        
        # Timestamp search feature
        ts_search = st.text_input("Search by timestamp (YYYY-MM-DD HH:MM:SS):")
        
        if search_query:
            df = df[df['text'].str.contains(search_query, case=False, na=False)]
            st.write(f"Search results: {len(df)} messages found.")
        
        if ts_search:
            try:
                ts_datetime = pd.to_datetime(ts_search)
                df = df[(df['ts'] == ts_datetime) | (df['thread_ts'] == ts_datetime)]
                st.write(f"Timestamp search results: {len(df)} messages found.")
            except ValueError:
                st.error("Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS format.")
        
        # Display data
        st.subheader(f'Data for {selected_channel} channel')

        # Display basic statistics
        st.subheader('Basic Statistics')
        fig = create_basic_statistics_figure(len(df), df['user'].nunique(), df['ts'].min().date(), df['ts'].max().date())
        st.plotly_chart(fig, use_container_width=True)
        
        # # Graph of messages per user
        # st.subheader('Messages per User')
        # user_counts = df['user'].value_counts()
        # st.bar_chart(user_counts)

        # Posts per day
        st.subheader('Posts per Day')
        df['date'] = df['ts'].dt.date

        # Create a complete date range
        date_range = pd.date_range(start=start_date, end=end_date)
        date_df = pd.DataFrame({'date': date_range.date})

        # Count posts per day
        posts_per_day = df.groupby('date').size().reset_index(name='count')

        # Merge with the complete date range, filling missing values with 0
        posts_per_day = pd.merge(date_df, posts_per_day, on='date', how='left').fillna(0)

        # Convert 'count' column to integer
        posts_per_day['count'] = posts_per_day['count'].astype(int)

        # Create the line chart
        fig = px.line(posts_per_day, x='date', y='count', title='Number of Posts per Day')
        fig.update_xaxes(title_text='Date')
        fig.update_yaxes(title_text='Number of Posts')

        # Customize hover information
        fig.update_traces(
            hovertemplate="<br>".join([
                "Date: %{x}",
                "Posts: %{y}",
            ])
        )

        st.plotly_chart(fig, use_container_width=True)

        # Display messages
        parent_messages = df[df['thread_ts'].isna() | (df['ts'] == df['thread_ts'])]
        parent_messages = parent_messages.sort_values('ts', ascending=(sort_order != "Newest first"))

        for _, msg in parent_messages.iterrows():
            st.text(f"{msg['user']} - {msg['ts']}")
            st.markdown(msg['text'])
            
            thread_messages = df[(df['thread_ts'] == msg['ts']) & (df['ts'] != msg['ts'])]
            if not thread_messages.empty:
                with st.expander("Show thread"):
                    thread_messages = thread_messages.sort_values('ts', ascending=True)
                    display_thread(thread_messages.to_dict('records'))
            
            st.markdown("---")
    else:
        st.info("Please select a channel.")

if __name__ == "__main__":
    main()