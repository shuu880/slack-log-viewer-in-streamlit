# slack-log-viewer-in-streamlit

A Streamlit application for visualizing and analyzing Slack Logs.

## Features

- Display Slack messages downloaded using slackdump
- Filter messages by date range
- Search messages by content or timestamp
- Show basic statistics and visualizations
- Display threaded conversations

## Prerequisites

- Python 3.8 or higher
- Streamlit
- Pandas
- Plotly

Installation:

```bash
pip install streamlit pandas plotly
```

## Setup

1. Clone the repository or download the source code

2. Place the JSON files extracted using slackdump in the `./dumps` folder.

The folder structure should be as follows:

```
dumps/
├── from_YYYY-MM-DD/
│   ├── channel1_YYYY-MM-DD.json
│   ├── channel2_YYYY-MM-DD.json
│   └── ...
├── from_YYYY-MM-DD/
│   ├── channel1_YYYY-MM-DD.json
│   ├── channel2_YYYY-MM-DD.json
│   └── ...
└── ...
```

## Running the Application

Execute the following command in your terminal:

```bash
streamlit run app.py
```
