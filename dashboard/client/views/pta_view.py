import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from ..db_utils import manager as db_manager 

def pta(request):
    device_params_selection = db_manager.get_device_configurations_selection()
    queryset = device_params_selection.values()

    # Logguer chaque élément du QuerySet comme un dictionnaire
    for item in queryset:
        print(item)
    return render(request, 'client/pta.html', {'device_params_selection': device_params_selection})

def download_device_configuration(request):
    # Récupérer les données du formulaire
    body = json.loads(request.body.decode("utf-8"))

    device_config = body['device_config']

    # Configuration factice du docteur
    # afin de simuler une configuration de docteur
    doctor_config = {
        "Couleur des yeux": "Marron",
        "Epaisseur de peau": "Epaisse",
        "Age": "35-49",
        "dummy": True
    }

    result = {
        "CC": doctor_config,
        "PTA": device_config
    }
    
    json_result = json.dumps(result, indent=4)

    # Créer une réponse HTTP avec le contenu JSON
    response = HttpResponse(json_result, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=device_configuration.json'
    return response
    