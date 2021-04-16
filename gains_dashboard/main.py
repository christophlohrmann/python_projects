# -*- coding: utf-8 -*-
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# get the gain data
df = pd.read_excel('./resources/the_gains.ods', engine='odf', header=[0, 1])
# Date has an empty second line, we need to fill the multiindex
date = df['Date'].copy()
date = date['Unnamed: 0_level_1']
# TODO this seems super ugly


categories = df.columns.get_level_values(0).unique().to_list()
categories.remove('Date')

user_wants = {'cat': categories[0],
              'relative': False}

app.layout = html.Div(children=[
    html.H1(children='Welcome to the GAINZ dashboard'),

    html.Div('Choose exercise'),
    dcc.Dropdown(
        id='dropdown_category',
        options=[{'label': cat, 'value': cat} for cat in categories],
        value=user_wants['cat']
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


@app.callback(
    dash.dependencies.Output('graph_gain', 'figure'),
    [dash.dependencies.Input('dropdown_category', 'value'),
     dash.dependencies.Input('toggle_switch_relative', 'value')])
def redraw_figure(dropdown_cat, toggle_rel):
    user_wants['cat'] = dropdown_cat
    user_wants['relative'] = toggle_rel
    return draw_figure(date, df, user_wants)


def draw_figure(date, df, user_wants):
    cat = user_wants['cat']
    relative = user_wants['relative']
    cat_data = df[cat]

    fig = go.Figure()
    for header in cat_data.columns.values:
        y = cat_data[header]
        if relative:
            y /= y[y.first_valid_index()]
        fig.add_trace(go.Scatter(x=date, y=y,
                                 mode='lines+markers',
                                 name=header,
                                 connectgaps=True))
    y_label = 'relative performance increase' if relative else 'weight'
    fig.update_layout(title=cat,
                      xaxis_title='Date',
                      yaxis_title=y_label,
                      legend_title_text='number of reps')

    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
