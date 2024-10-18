import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.http import JsonResponse
from ..db_utils import manager as db_manager 

def pta(request):
    doctor_params_with_values = db_manager.get_doctor_configurations()
    device_params_selection = db_manager.get_device_configurations_selection()
    configuration_pairings = db_manager.get_configuration_pairings()

    return render(
        request, 
        'client/pta.html', 
        {
            'doctor_params_with_values': doctor_params_with_values, 
            'device_params_selection': device_params_selection,
        }
    )

def get_configuration_pairings(request):
    configuration_pairings = db_manager.get_configuration_pairings()
    return JsonResponse(configuration_pairings, safe=False)

@csrf_exempt
@require_POST
def add_configuration_rule(request):
    # Récupérer les données du formulaire
    body = json.loads(request.body.decode("utf-8"))

    doctor_config = body['doctor_config']
    device_config = body['device_config']

    db_manager.update_configuration_rule(doctor_config, device_config)

    configuration_pairings = db_manager.get_configuration_pairings()

    return JsonResponse(configuration_pairings, safe=False)

    