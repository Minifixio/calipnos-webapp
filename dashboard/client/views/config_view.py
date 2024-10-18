import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from ..db_utils import manager as db_manager 

def config(request):
    params_with_values = db_manager.get_doctor_configurations()
    return render(request, 'client/config.html', {'params_with_values': params_with_values})

def download_device_configuration(request):
    # Récupérer les données du formulaire
    body = json.loads(request.body.decode("utf-8"))

    doctor_config_ids = body['doctor_config_ids']
    doctor_config = body['doctor_config']

    device_config = db_manager.get_device_configuration_from_doctor_configuration(doctor_config_ids)
    print("Device config:")
    print(device_config)

    result = {
        "CC": doctor_config,
        "PTA": device_config
    }
    
    json_result = json.dumps(result, indent=4)

    # Créer une réponse HTTP avec le contenu JSON
    response = HttpResponse(json_result, content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename=device_configuration.json'
    return response
    