# -*- coding: utf-8 -*-
# visit http://127.0.0.1:8050/ in your web browser.

import dash
import dash_core_components as dcc
import dash_html_components as html
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

def plot_category(date, df, cat, relative=True):
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


fig = plot_category(date, df, 'Curl', relative=True)

app.layout = html.Div(children=[
    html.H1(children='Welcome to the GAINZ dashboard'),

    html.Div(children='have fun'),
    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True)
