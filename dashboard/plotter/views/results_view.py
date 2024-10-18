import io
import json
import plotly
import pandas as pd

import plotly.graph_objects as go

from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from ..csv_processing import csv_processing as cp
from ..metrics import Metric 
from ..constants import AppConstants, ProcessingConstants
from ..forms import MetricForm

# Les données, mises à jour lors de l'upload du CSV
data = None
buffer = None

# Les paramètres de traitement des données
filter_params = ProcessingConstants.DEFAULT_FILTER_PARAMS
event_det_params = ProcessingConstants.DEFAULT_EVENT_DET_PARAMS

# Les paramètres de traitement des données
customizable_params = {
    "spO2_low_threshold": {
        "value": 80,
        "name": "Seuil bas SpO2",
        "color": "blue",
        "max": 100,
        "min": 10,
    }, 
    "spO2_high_threshold": {
        "value": 100,
        "name": "Seuil haut SpO2",
        "color": "blue",
        "max": 120,
        "min": 10
    },
    "cardio_low_threshold": {
        "value": 40,
        "name": "Seuil bas cardio",
        "color": "blue",
        "max": 100,
        "min": 20
    },
    "cardio_high_threshold": {
        "value": 120,
        "name": "Seuil haut cardio",
        "color": "blue",
        "max": 140,
        "min": 20
    },
    "window_size": {
        "value": 9,
        "name": "Fenêtre d'échantillonnage",
        "color": "orange",
        "max": 100,
        "min": 1
    }
}

def multi_graph(metrics=None, json_graph=False):
    global data

    local_data = data.copy()

    # On crée le graphique
    fig = go.Figure()

    # On combine les colonnes Date et Time en une seule valeur de temps Datetime
    local_data['Datetime'] = pd.to_datetime(local_data['Date'] + ' ' + local_data['Time'], format='%d/%m/%Y %H:%M:%S')

     # On ajoute le sélécteur de date
    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(step="all",
                         label="tout"),
                    dict(count=1,
                        label="1h",
                        step="hour",
                        stepmode="backward"),
                    dict(count=2,
                        label="2h",
                        step="hour",
                        stepmode="backward"),
                    dict(count=30,
                        label="30min",
                        step="minute",
                        stepmode="backward"),
                    dict(count=20,
                        label="20sec",
                        step="second",
                        stepmode="backward")
                ]),
                x=0.1,
                y=1.1,
            ),
            rangeslider=dict(
                visible=True
            ),
            type="date"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
    )

    yaxis_configurations = {}

    # nécessaire pour afficher le titre proprepement si il y qu'une seule métrique
    if (len(metrics) == 1):
        fig.add_trace(go.Scatter(
            x=local_data['Datetime'], 
            y=local_data[metrics[0].value], 
            mode='lines', 
            name=metrics[0].value,
            yaxis="y"
        ))
        yaxis_configurations = dict(
            title={
            'text': metrics[0].value,
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'}
        ) 
    
    # sinon on affiche les métriques sur des axes différents
    else:
        for idx, metric in enumerate(metrics):

            sidx = ''
            
            if (idx == 0): sidx = ''
            else: sidx = str(idx + 1)
            
            fig.add_trace(go.Scatter(
                x=local_data['Datetime'], 
                y=local_data[metric.value], 
                mode='lines', 
                name=metric.value,
                yaxis="y"+sidx
            ))

            yaxis_configurations["yaxis" + sidx] = dict(
                anchor="x",
                autorange=True,
                domain=[idx/len(metrics), (idx+1)/len(metrics)],
                linecolor="#673ab7",
                mirror=True,
                showline=True,
                side="right",
                titlefont={"color": "#673ab7"},
                type="linear",
                zeroline=False
            )

    fig.update_layout(**yaxis_configurations)

    # On convertit le graphique en html
    graph = fig.to_html(full_html=True, default_width='80vw', default_height='100vh', div_id='graph')
    if json_graph: graph = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graph


def update_params(params):
    global filter_params, event_det_params

    for key, value in params.items():
        if key in filter_params:
            filter_params[key] = int(value)
        if key in event_det_params:
            event_det_params[key] = int(value)


# Vérifie si les paramètres de traitement ont changé
# afin de savoir si on doit retraiter les données
def params_differ(params):
    global filter_params, event_det_params

    for key, value in params.items():
        if key in filter_params:
            if int(value) != filter_params[key]: 
                return True
        if key in event_det_params:
            if int(value) != event_det_params[key]:
                return True

    return False


# fonction appelée lors de l'upload d'un fichier csv
# ou bien lors de la modification des paramètres de traitement
@csrf_exempt
@require_POST
def change_graph_params(request):

    global data, csv, filter_params, event_det_params

    if data is None:
        return HttpResponseNotFound("Pas de données à afficher")

    raw_metrics = list(json.loads(request.body.decode("utf-8"))['metrics'])
    selected_metrics = [Metric[value] for value in raw_metrics]

    params = json.loads(request.body.decode("utf-8"))['params']

    if params_differ(params):
        update_params(params)
        copied_buffer = io.StringIO(buffer.getvalue())
        csv_processed = cp.process_csv_buffer(copied_buffer, ProcessingConstants.DEFAULT_FILTER_PARAMS, ProcessingConstants.DEFAULT_EVENT_DET_PARAMS, plot=False, event_detection=True)
        data = pd.concat(csv_processed, ignore_index=False)

    graph = multi_graph(metrics=selected_metrics, json_graph=True)

    return HttpResponse(graph)

@csrf_exempt
@require_POST
def change_graph_data(request):

    global data, buffer

    # On récupère les données csv depuis le contenue de la requête POST
    csv = request.FILES.get('csv')

    # On passe le csv dans un buffer qui va ensuite être traité
    buffer = io.StringIO(csv.read().decode("utf-8"))
    copied_buffer = io.StringIO(buffer.getvalue())
    try:
        csv_processed = cp.process_csv_buffer(copied_buffer, ProcessingConstants.DEFAULT_FILTER_PARAMS, ProcessingConstants.DEFAULT_EVENT_DET_PARAMS, plot=False, event_detection=True)

        # On concatène les différents DataFrame issus du traitement initial du csv
        data = pd.concat(csv_processed, ignore_index=False)

        graph = multi_graph([Metric.SATURATION, Metric.CARDIO, Metric.AUDIO, Metric.MOVEMENT, Metric.SILENCE, Metric.GLOBAL], json_graph=True)

        return HttpResponse(graph)
    
    except Exception as e:
        return HttpResponseNotFound(e)
    


@login_required
def results(request):

    # Si on a pas de données à afficher, on affiche un graph vide
    graph = None
    fig = go.Figure()
    fig.update_layout(
        title="Pas de données à afficher",
    )

    graph = fig.to_html(full_html=True, default_width='80vw', default_height='100vh', div_id='graph')

    form = MetricForm()

    params = filter_params.copy() 
    params.update(event_det_params)

    return render(request, 'plotter/results.html', {'form': form, 'graph': graph, 'params': customizable_params})