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
import datetime

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
    oldest = newest.sort_values(by='date')
    return oldest.iloc[0:number]


def generate_gain_table(df):
    display_cols = ['date', 'type', 'subtype']
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in display_cols])
        ),
        html.Tbody(
            [html.Tr([html.Td(row[col]) for col in display_cols]) for _, row in df.iterrows()]
        )])


def generate_old_gain_table(df, max_rows):
    oldest = get_oldest_pr(df, max_rows)
    return generate_gain_table(oldest)


def generate_new_gain_table(df, max_rows):
    sorted_df = df.sort_values(by='date', ascending=False)
    return generate_gain_table(sorted_df.iloc[0:max_rows])

def append_new_gain_to_database(new_gain, conn):
    df = new_gain.to_data_frame()
    df.to_sql('the_gains', conn, if_exists = 'append', index = False)


external_stylesheets = [dbc.themes.LITERA]  # ['https://codepen.io/chriddyp/pen/bWLwgP.css']

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
            id='dropdown_goal',
            clearable=False
        )]),

    dcc.Graph(
        id='graph_gain',
        figure={}
    ),
    html.Br(),
    daq.ToggleSwitch(
        id='toggle_switch_relative',
        value=False,
        label=['display absolute values', 'display relative increase'],
        labelPosition='bottom')

])

card_table = dbc.Card([
    dbc.CardBody([
        html.H4('Your top 5 newest gains'),
        html.Br(),
        generate_new_gain_table(df, max_rows=5),
        html.Br(),
        html.H4('Your top 5 oldest gains that could use some work'),
        html.Br(),
        generate_old_gain_table(df, max_rows=5)

    ])
])

card_submit = dbc.Card([
    dbc.CardBody([
        html.H4('Submit a new gain from previous types'),
        html.Br(),
        html.H6('Exercise type'),
        dcc.Dropdown(
            id='dropdown_form_old_type',
            options=[{'label': type, 'value': type} for type in all_types],
            clearable=False),
        html.Br(),
        html.H6('Exercise subtype'),
        dcc.Dropdown(
            id='dropdown_form_old_subtype',
            clearable=False),
        html.Br(),
        html.H6('goal'),
        dcc.Dropdown(
            id='dropdown_form_old_goal',
            options=[{'label': goal, 'value': goal} for goal in all_goals],
            clearable=False),
        html.Br(),
        html.H6('weight in kg'),
        dcc.Input(
            id='input_form_old_weight',
            value=0.,
            type='number',
            placeholder='weight'
        ),
        html.Br(),
        html.H6('number of repetitions'),
        dcc.Input(
            id='input_form_old_reps',
            value=0,
            type='number',
            placeholder='number or reps',
        ),
        html.Br(),
        html.H6('time in seconds'),
        dcc.Input(
            id='input_form_old_time',
            value=0.,
            type='number',
            placeholder='time in seconds',
        ),
        html.Br(),
        html.Button(id='button_form_old_submit',
                    n_clicks=0,
                    children='Submit'),
        html.Br(),
        html.Div(id='output_submit_status')

    ])
])


@app.callback(dash.dependencies.Output('dropdown_form_old_subtype', 'options'),
              dash.dependencies.Input('dropdown_form_old_type', 'value'))
def set_subtype_options(type_):
    # don't use global df
    available_subtypes = df[df['type'] == type_]['subtype'].unique().tolist()
    return [{'label': subtype, 'value': subtype} for subtype in available_subtypes]

@app.callback(dash.dependencies.Output('output_submit_status', 'children'),
              dash.dependencies.Input('button_form_old_submit','n_clicks'),
              dash.dependencies.State('dropdown_form_old_type', 'value'),
              dash.dependencies.State('dropdown_form_old_subtype', 'value'),
              dash.dependencies.State('dropdown_form_old_goal', 'value'),
              dash.dependencies.State('input_form_old_weight', 'value'),
              dash.dependencies.State('input_form_old_reps', 'value'),
              dash.dependencies.State('input_form_old_time', 'value'))
def handle_submit_update_status(n_clicks, type_, subtype,goal, weight, reps, time):
    if n_clicks>0:
        new_gain = resources.gain.Gain(type_,
                                       datetime.date.today(),
                                       subtype=subtype,
                                       goal=goal,
                                       weight=weight,
                                       reps=reps,
                                       time=time)
        sql_conn = sqlite3.connect('./resources/the_gains.db')
        append_new_gain_to_database(new_gain, sql_conn)
        return f'new gain submitted at {datetime.datetime.now()}'
    else:
        return ''


app.layout = html.Div([
    html.H1('Welcome to the GAINZ dashboard'),
    dbc.CardDeck([card_graph, card_table, card_submit])
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
