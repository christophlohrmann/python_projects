# -*- coding: utf-8 -*-
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.subplots
import plotly.graph_objects as go
import pandas as pd
import sqlite3
import numpy as np

import resources.gain


def get_oldest_pr(df_, number):
    # get the newest entry of all subtypes
    df = df_.copy()
    newest = pd.DataFrame()
    for type in df['type'].unique():
        df_type = df[df['type'] == type]
        for subtype in df_type['subtype'].unique():
            df_subtype = df_type[df_type['subtype'] == subtype]
            df_subtype = df_subtype.sort_values(by='date', ascending=False)
            newest = newest.append(df_subtype.iloc[0])
    newest = newest.sort_values(by='date')
    return newest.iloc[0:number]


def generate_old_gain_table(df, max_rows = 5):
    oldest = get_oldest_pr(df, max_rows)
    display_cols = ['date', 'type', 'subtype']
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in display_cols])
        ),
        html.Tbody(
            [html.Tr([html.Td(oldest.iloc[i][col]) for col in display_cols]) for i in range(max_rows)]
        )])



external_stylesheets =[dbc.themes.LITERA] #['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# get the new_gain data
sql_conn = sqlite3.connect('./resources/the_gains.db')
df = pd.read_sql('SELECT * FROM the_gains', sql_conn)

all_types = df['type'].unique().tolist()
all_goals = resources.gain.ALLOWED_GOALS


card_graph = dbc.Card([
    dbc.CardBody([
        html.H6('Choose exercise', className='card_subtitle'),
        dcc.Dropdown(
            id='dropdown_type',
            options=[{'label': type, 'value': type} for type in all_types],
            value=all_types[0]
        ),

        html.Br(),

        html.H6('Choose goal', className='card_subtitle'),
        dcc.Dropdown(
            id='dropdown_goal'
        )]),

        dcc.Graph(
            id='graph_gain',
            figure={}
        ),
        html.Br(),
        daq.ToggleSwitch(
            id='toggle_switch_relative',
            value=False,
            label='display relative increase',
            labelPosition='bottom')

])

card_table = dbc.Card([
    dbc.CardBody([
        html.H4('Your top 5 oldest gains that could use some work'),
        html.Br(),
        generate_old_gain_table(df, max_rows=5)
    ])
])

app.layout = html.Div([
    html.H1('Welcome to the GAINZ dashboard'),
    dbc.CardDeck([card_graph, card_table])
])

y_labels = {'weight': 'weight in kg',
            'reps': 'number of repetitions',
            'time': 'time in seconds',
            'goal_relative': 'relative performance increase'}


@app.callback(dash.dependencies.Output('dropdown_goal', 'options'),
              dash.dependencies.Input('dropdown_type', 'value'))
def set_goal_options(type_):
    available_goals = df[df['type'] == type_]['goal'].unique().tolist()
    return [{'label': goal, 'value': goal} for goal in available_goals]


@app.callback(dash.dependencies.Output('dropdown_goal', 'value'),
              dash.dependencies.Input('dropdown_goal', 'options'))
def set_goal_default_value(options):
    return options[0]['value']


@app.callback(
    dash.dependencies.Output('graph_gain', 'figure'),
    [dash.dependencies.Input('dropdown_type', 'value'),
     dash.dependencies.Input('dropdown_goal', 'value'),
     dash.dependencies.Input('toggle_switch_relative', 'value')])
def redraw_figure(dropdown_type, dropdown_goal, toggle_rel):
    user_wants = dict()
    user_wants['type'] = dropdown_type
    user_wants['relative'] = toggle_rel
    user_wants['goal'] = dropdown_goal
    return draw_figure(df, user_wants)


def draw_figure(df, user_wants):
    type_ = user_wants['type']
    goal = user_wants['goal']
    relative = user_wants['relative']

    # find which subtypes are compatible with type and goal
    df_filtered = df[df['type'] == type_].copy()
    df_filtered = df_filtered[df_filtered['goal'] == goal]

    if relative:
        # split the dataframes according to the group_by value
        group_vals = df_filtered['subtype'].unique()
        grouped_dfs = [df_filtered[df_filtered['subtype'] == group_val].copy() for group_val in group_vals]
        df_filtered = pd.DataFrame()
        # perform the division and stitch the frame back together
        for grouped_df in grouped_dfs:
            grouped_df.sort_values(by='date')
            grouped_df['goal_relative'] = grouped_df[goal] / grouped_df[goal].iloc[0]
            df_filtered = df_filtered.append(grouped_df, ignore_index=True)

    goal = 'goal_relative' if relative else goal
    fig = px.line(df_filtered, x='date', y=goal, color='subtype', labels=y_labels)
    fig.update_layout()

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
