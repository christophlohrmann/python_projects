# -*- coding: utf-8 -*-
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.express as px
import plotly.subplots
import plotly.graph_objects as go
import pandas as pd
import numpy as np

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# get the gain data
df = pd.read_pickle('./resources/the_gains.pick')

all_types = df['type'].unique().tolist()
all_goals = df['goal'].unique().tolist()

user_wants = {'cat': all_types[0],
              'goal': all_goals[0],
              'group_by': all_goals[1],
              'relative': False}

app.layout = html.Div(children=[
    html.H1(children='Welcome to the GAINZ dashboard'),

    html.Div('Choose exercise'),
    dcc.Dropdown(
        id='dropdown_type',
        options=[{'label': type, 'value': type} for type in all_types],
        value=user_wants['cat']
    ),

    html.Div('Choose goal'),
    dcc.Dropdown(
        id='dropdown_goal',
        options=[{'label': goal, 'value': goal} for goal in all_goals],
        value=user_wants['goal']
    ),

    html.Div('Group by'),
    dcc.Dropdown(
        id='dropdown_group_by',
        options=[{'label': goal, 'value': goal} for goal in all_goals],
        value=user_wants['group_by']
    ),

    dcc.Graph(
        id='graph_gain',
        figure={}
    ),
    html.Br(),

    daq.ToggleSwitch(
        id='toggle_switch_relative',
        value=user_wants['relative'],
        label='display relative increase',
        labelPosition='bottom'
    )
])

y_labels = {'weight': 'weight in kg',
            'reps': 'number of repetitions',
            'time': 'time in seconds',
            'goal_relative': 'relative performance increase'}


@app.callback(
    dash.dependencies.Output('graph_gain', 'figure'),
    [dash.dependencies.Input('dropdown_type', 'value'),
     dash.dependencies.Input('dropdown_goal', 'value'),
     dash.dependencies.Input('dropdown_group_by', 'value'),
     dash.dependencies.Input('toggle_switch_relative', 'value')])
def redraw_figure(dropdown_type, dropdown_goal, dropdown_group_by, toggle_rel):
    user_wants['cat'] = dropdown_type
    user_wants['relative'] = toggle_rel
    user_wants['goal'] = dropdown_goal
    user_wants['group_by'] = dropdown_group_by
    return draw_figure(df, user_wants)


def draw_figure(df, user_wants):
    type_ = user_wants['cat']
    goal = user_wants['goal']
    group_by = user_wants['group_by']
    relative = user_wants['relative']

    not_goal = all_goals.copy()
    not_goal.remove(goal)

    relevant_gains = df[df['type'] == type_].copy()
    relevant_gains = relevant_gains[relevant_gains['goal'] == goal]

    if relative:
        # split the dataframes according to the group_by value
        group_vals = relevant_gains[group_by].unique()
        grouped_dfs = [relevant_gains[relevant_gains[group_by] == group_val].copy() for group_val in group_vals]
        relevant_gains = pd.DataFrame()
        # perform the division and stitch the frame back together
        for grouped_df in grouped_dfs:
            grouped_df.sort_values(by='date')
            grouped_df['goal_relative'] = grouped_df[goal] / grouped_df[goal].iloc[0]
            relevant_gains = relevant_gains.append(grouped_df, ignore_index=True)

    goal = 'goal_relative' if relative else goal
    fig = px.line(relevant_gains, x='date', y=goal, color=group_by, hover_data=not_goal,
                  labels=y_labels)
    fig.update_layout()

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
