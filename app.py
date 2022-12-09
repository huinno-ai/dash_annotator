# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
from plotly.callbacks import Points, InputDeviceState
import pandas as pd
import os
import numpy as np
import copy
import json
from dash.exceptions import PreventUpdate
#######################################################################################
#path = 'annotation_tool/data/'
path = 'data/'
filelist = os.listdir(path)

# Target patient ID
data_total = pd.read_pickle(path+filelist[0])
# Select target data
filenames = data_total['filename']
# ECG Graph
idx = 0
data = data_total['signal'][int(idx*2500):int(int(idx+1)*2500)]

beat_list = ['N','A','V','Q']
rhythm_list = ['SVT','VT','AF','Noise', 'AVB']
#######################################################################################
# ECG
fig = go.FigureWidget()
ecg_range = np.arange(0,len(data))
fig.add_trace(go.Scatter(x=ecg_range,
                         y=data,
                         mode='lines',
                         name='lines'))
fig.update_layout(
    #yaxis_range=[-4,4],
    clickmode='select',
    dragmode='drawrect',

    width=1600,
    height=600,

    hovermode='x',
    spikedistance=-1,

    xaxis=dict(showspikes=True,
               spikemode='across',
               spikesnap='cursor',
               spikecolor='grey',
               spikedash='solid',
               spikethickness=1,
               showline=True,
               showgrid=False),
    yaxis=dict(showgrid=False)
)


# Draw fixed grid line
freq_ = 250
x_tic = []
x_label = []
freq = int((freq_ / 5))
sec_ = 0
for x in range(0, int(len(data) / freq) + 1):
    x_tic.append(int(freq * x))
    if int((freq * x) % 250) == 0:
        x_label.append(str(sec_))
        sec_ += 1
    else:
        x_label.append('')
y_tic = [-3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

for x_ in range(0,len(x_tic)):
    fig.add_vline(x=x_tic[x_],
                  annotation_text=x_label[x_],
                  annotation_position='bottom left',
                  opacity=0.5, line_width=1
                  )
for y_ in range(0,len(y_tic)):
    fig.add_hline(y=y_tic[y_],
                  opacity=0.5, line_width=1
                  )



# Rhythm
rhythm_idx = data_total['rhythm']['index'][0]
rhythm_annotation = data_total['rhythm']['annotation'][0]

ply_shapes = {}
fig.add_shape(type="rect",
              editable=True,
              layer='above',
              y0=-3, y1=3,
              x0=rhythm_idx[0], x1=rhythm_idx[1],
              fillcolor="yellow", opacity=0.2, line_width=0)
lst_shapes = list(ply_shapes.values())
fig.update_layout(shapes=lst_shapes)

# Beat
beat_idx = data_total['beat']['index'][0]
beat_annotation = data_total['beat']['annotation'][0]

ply_shapes = {}
for b in range(0, len(beat_idx)):
    fig.add_shape(type="line",
                  editable=True,
                  layer='above',
                  x0=beat_idx[b],
                  y0=-3,
                  x1=beat_idx[b],
                  y1=3,
                  line=dict(color="red"),
                  opacity=0.5, line_width=2
                  )

lst_shapes = list(ply_shapes.values())
fig.update_layout(shapes=lst_shapes)


####################################################################################################


config = dict({'scrollZoom': True,
               'displayModeBar': True,
               'displaylogo': False,
               'modeBarButtonsToAdd':['drawline',
                                      'drawopenpath',
                                      'drawclosedpath',
                                      'drawcircle',
                                      'drawrect',
                                      'eraseshape']
               })
####################################################################################################
# Plot image

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
app = dash.Dash()

app.layout = dash.html.Div([
    # Data information
    dash.html.H3(children=filenames[idx]),
    # Exclusion button
    dash.dcc.Checklist(['Exclusion']),
    # ECG graph
    dash.dcc.Graph(id='ecg_plot',figure=fig, config=config),
    #
    dash.html.Div(id="x_pos",children='X position'),
    # Comment
    dash.dcc.Textarea(placeholder='Comment', value='',
                      style={'width': '100%'}),
    # Save butten
    dash.html.Button('SAVE', id='button-example-1'),
    dash.html.Div(id='output-container-button',
                  children='Press SAVE after annotation'),
    # Annotation tab
    dash.dcc.Tabs(id="tabs", value='tab-1',
                  children=[dash.dcc.Tab(label='Beat', value='tab-1'),
                            dash.dcc.Tab(label='Rhythm', value='tab-2'),]),
    dash.html.Div(id='tabs-content'),
    dash.dcc.Upload(id='upload-data',
                    children=dash.html.Div(['Drag and Drop or ',dash.html.A('Select Files')]),
                    style = {'width': '100%',
                             'height': '60px',
                             'lineHeight': '60px',
                             'borderWidth': '1px',
                             'borderStyle': 'dashed',
                             'borderRadius': '5px',
                             'textAlign': 'center',
                             'margin': '10px'}
                    ),
                    dash.html.Div(id='output-data-upload'),
])
new_idx = []


def parse_contents(path):
    children = os.listdir(path)
    return children

@app.callback(Output('upload-data', 'children'),
              Input('upload-data', 'folder_path'))
def update_output(folder_path):
    children = parse_contents(folder_path)
    return children


@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'))
def render_content(tab):
    global beat_list
    global rhythm_list
    if tab == 'tab-1':
        return dash.html.Div([
            dash.dcc.RadioItems(beat_list, beat_list[0])
        ])
    elif tab == 'tab-2':
        return dash.html.Div([
            dash.dcc.RadioItems(rhythm_list, rhythm_list[0])
        ])

@app.callback(Output("x_pos",  "children"),
              Input("ecg_plot", "clickData"))
def get_click(clickData):
    global new_idx
    if not clickData:
        raise PreventUpdate
    else:
        points = clickData.get('points')[0]
        x = points.get('x')
        new_idx.append(x)

    if len(new_idx)!=0:
        new_idx = []
        ply_shapes = {}
        fig.add_shape(type="line",
                      editable=True,
                      layer='above',
                      x0=new_idx[0],
                      y0=-3,
                      x1=new_idx[0],
                      y1=3,
                      line=dict(color="red"),
                      opacity=0.5, line_width=2
                      )

        lst_shapes = list(ply_shapes.values())
        fig.update_layout(shapes=lst_shapes)

if __name__ == '__main__':
    app.run_server(debug=True)
