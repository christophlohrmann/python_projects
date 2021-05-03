# -*- coding: utf-8 -*-
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import sqlite3
import datetime

import resources.gain

external_stylesheets = [dbc.themes.SPACELAB]  # ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# get the new_gain data
sql_conn = sqlite3.connect('./resources/the_gains.db')
df = pd.read_sql('SELECT * FROM the_gains', sql_conn)

all_types = df['type'].unique().tolist()
all_goals = resources.gain.ALLOWED_GOALS

y_labels = {'weight': 'weight in kg',
            'reps': 'number of repetitions',
            'time': 'time in seconds',
            'goal_relative': 'relative performance increase'}

def generate_gain_table(df):
    return dbc.Table.from_dataframe(df[['date', 'type', 'subtype']],
                                    bordered=True,
                                    hover=True,
                                    responsive=True,
                                    striped=True)


def append_new_gain_to_df_and_db(new_gain, conn):
    # TODO keep this only as long as we work with the df instead of querying the data from the db directly
    global df
    df = df.append(new_gain.to_data_frame(), ignore_index=True)
    df.to_sql('the_gains', conn, if_exists='append', index=False)
    return df


def delete_last_row_from_df_and_db(conn):
    # TODO this is literally the most inefficient way to do this.
    # should be replaced by immediate action on the database, not through dataframe
    df.sort_index(inplace=True)
    df.drop(df.tail(1).index, inplace=True)
    df.to_sql('the_gains', conn, if_exists='replace', index=False)

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
    return oldest.head(number)


@app.callback(dash.dependencies.Output('dropdown_form_old_subtype', 'options'),
              dash.dependencies.Input('dropdown_form_old_type', 'value'))
def set_subtype_options(type_):
    # don't use global df
    available_subtypes = df[df['type'] == type_]['subtype'].unique().tolist()
    return [{'label': subtype, 'value': subtype} for subtype in available_subtypes]


@app.callback(dash.dependencies.Output('output_submit_status', 'children'),
              dash.dependencies.Input('button_form_old_submit', 'n_clicks'),
              dash.dependencies.State('dropdown_form_old_type', 'value'),
              dash.dependencies.State('dropdown_form_old_subtype', 'value'),
              dash.dependencies.State('dropdown_form_old_goal', 'value'),
              dash.dependencies.State('input_form_old_weight', 'value'),
              dash.dependencies.State('input_form_old_reps', 'value'),
              dash.dependencies.State('input_form_old_time', 'value'))
def handle_submit_update_status(n_clicks, type_, subtype, goal, weight, reps, time):
    if n_clicks > 0:
        print('submit requested')
        try:
            new_gain = resources.gain.Gain(type_,
                                           datetime.date.today(),
                                           subtype=subtype,
                                           goal=goal,
                                           weight=weight,
                                           reps=reps,
                                           time=time)
            sql_conn = sqlite3.connect('./resources/the_gains.db')
            append_new_gain_to_df_and_db(new_gain, sql_conn)

            return dbc.Alert(f'new gain submitted at {datetime.datetime.now()}',
                             color='success')
        except Exception as e:
            print(e)
            return dbc.Alert(f'submitting of a new gain failed',
                             color='danger')
    else:
        return ''


@app.callback(dash.dependencies.Output('output_remove_status', 'children'),
              dash.dependencies.Input('button_form_old_remove', 'n_clicks'))
def handle_remove_update_status(n_clicks):
    if n_clicks > 0:
        print('removal requested')
        try:
            sql_conn = sqlite3.connect('./resources/the_gains.db')
            delete_last_row_from_df_and_db(sql_conn)
            return dbc.Alert(f'newest entry removed',
                             color='success')
        except Exception:
            return dbc.Alert(f'failed to remove the newest entry',
                             color='danger')
    else:
        return ''


@app.callback(dash.dependencies.Output('table_oldest_gains', 'children'),
              dash.dependencies.Input('button_form_old_submit', 'n_clicks'),
              dash.dependencies.Input('button_form_old_remove', 'n_clicks'))
def generate_old_gain_table(n_clicks_submit, n_clicks_remove, max_rows=5):
    print('generating old table')
    disp_rows = min([max_rows, len(df.index)])
    oldest = get_oldest_pr(df, disp_rows)
    return generate_gain_table(oldest)


@app.callback(dash.dependencies.Output('table_newest_gains', 'children'),
              dash.dependencies.Input('button_form_old_submit', 'n_clicks'),
              dash.dependencies.Input('button_form_old_remove', 'n_clicks'))
def generate_new_gain_table(n_clicks_submit, n_clicks_remove, max_rows=5):
    print('generating new table')
    disp_rows = min([max_rows, len(df.index)])
    sorted_df = df.sort_values(by='date', ascending=False).copy()
    return generate_gain_table(sorted_df.head(disp_rows))


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
     dash.dependencies.Input('toggle_switch_relative', 'value'),
     dash.dependencies.Input('button_form_old_submit', 'n_clicks'),
     dash.dependencies.Input('button_form_old_remove', 'n_clicks')])
def redraw_figure(dropdown_type, dropdown_goal, toggle_rel, n_clicks_submit, n_clicks_remove):
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


card_graph = dbc.Card([
    dbc.CardBody([
        html.H6('Choose exercise', className='card_subtitle'),
        dcc.Dropdown(
            id='dropdown_type',
            options=[{'label': type, 'value': type} for type in all_types],
            value=all_types[0],
            clearable=False
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
        dbc.Table(id='table_newest_gains'),
        #          children=generate_new_gain_table(df, max_rows=5)),
        html.Br(),
        html.H4('Your top 5 oldest gains that could use some work'),
        html.Br(),
        dbc.Table(id='table_oldest_gains')  # ,
        # children=generate_old_gain_table(df, max_rows=5))

    ])
])

card_submit = dbc.Card([
    dbc.CardBody([
        html.H4('Submit a new gain'),
        dbc.Form([
            dbc.FormGroup([
                dbc.Label('Exercise type'),
                dcc.Dropdown(
                    id='dropdown_form_old_type',
                    options=[{'label': type, 'value': type} for type in all_types],
                    clearable=False)
            ]),
            dbc.FormGroup([
                dbc.Label('Exercise subtype'),
                dcc.Dropdown(
                    id='dropdown_form_old_subtype',
                    clearable=False)
            ]),
            dbc.FormGroup([
                dbc.Label('goal'),
                dcc.Dropdown(
                    id='dropdown_form_old_goal',
                    options=[{'label': goal, 'value': goal} for goal in all_goals],
                    clearable=False)
            ]),
            dbc.FormGroup([
                dbc.Label('Weight in kg'),
                dbc.Input(
                    id='input_form_old_weight',
                    value=0.,
                    type='number',
                    placeholder='weight'
                )
            ]),
            dbc.FormGroup([
                dbc.Label('number of repetitions'),
                dbc.Input(
                    id='input_form_old_reps',
                    value=0,
                    type='number',
                    placeholder='number or reps',
                )
            ]),
            dbc.FormGroup([
                dbc.Label('time in seconds'),
                dbc.Input(
                    id='input_form_old_time',
                    value=0.,
                    type='number',
                    placeholder='time in seconds',
                )
            ]),
            html.Br(),
            dbc.Button(id='button_form_old_submit',
                       n_clicks=0,
                       children='Submit',
                       color='primary'),
            html.Br(),
            html.Div(id='output_submit_status'),
            html.Br(),
            dbc.Button(id='button_form_old_remove',
                       n_clicks=0,
                       children='Remove last entry',
                       color='warning'),
            html.Br(),
            html.Div(id='output_remove_status')
        ]),  # end form

    ])  # end card body
])

app.layout = html.Div([
    html.H1('Welcome to the GAINZ dashboard'),
    dbc.CardDeck([card_graph, card_table, card_submit])
])

if __name__ == '__main__':
    app.run_server(debug=True)
