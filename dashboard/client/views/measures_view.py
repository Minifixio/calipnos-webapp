from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from ..db_utils import manager as db_manager 
from django.http import HttpResponse
import csv

def measures(request):
    return render(request, 'client/measures.html')

@csrf_exempt
@require_POST
def upload_binary(request):

    # On récupère les données csv depuis le contenue de la requête POST
    bin = request.FILES.get('bin')

    print(f"Received binary file: {bin.name}")
   
    if 'bin' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)

    # Récupération du fichier binaire
    bin_file = request.FILES['bin']
    file_content = bin_file.read()  # Lecture complète du fichier binaire

    try:
        # Ajout de la nouvelle mesure via measures_handler
        db_manager.add_measure(file_content)

        # Récupérer la liste des mesures après l'ajout
        measures = db_manager.get_measures()

        # Convertir le QuerySet en liste de dictionnaires
        measures_data = list(measures.values(
            'id', 'version', 'upload_date', 'start_time', 'end_time', 'points_count'
        ))

        res = [
            {
                'id': measure['id'],
                'version': measure['version'],
                'upload_date': measure['upload_date'].strftime('%Y-%m-%d %H:%M:%S'),
                'duration': (measure['end_time'] - measure['start_time']).total_seconds(),
                'points_count': measure['points_count']
            }
            for measure in measures_data
        ]

        # Retourne la liste complète de mesures au format JSON
        return JsonResponse(res, safe=False)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def get_measures(request):
    """
    Récupère toutes les mesures de la base de données et les renvoie sous forme de JSON.
    """
    measures = db_manager.get_measures()

    # Convertir le QuerySet en liste de dictionnaires
    measures_data = list(measures.values(
        'id', 'version', 'upload_date', 'start_time', 'end_time', 'points_count'
    ))

    res = [
        {
            'id': measure['id'],
            'version': measure['version'],
            'upload_date': measure['upload_date'].strftime('%Y-%m-%d %H:%M:%S'),
            'duration': (measure['end_time'] - measure['start_time']).total_seconds(),
            'points_count': measure['points_count']
        }
        for measure in measures_data
    ]

    return JsonResponse(res, safe=False)

@csrf_exempt
@require_POST
def delete_measure(request, measure_id):
    """
    Supprime une mesure basée sur son ID.
    """
    try:
        # Récupérer l'objet à supprimer
        measure = db_manager.delete_measure(measure_id)
        if not measure:
            # TODO: changer le statut 404 de la réponse
            return JsonResponse({'error': 'Measure not found.'}, status=404)
        
        return JsonResponse({'success': 'Measure deleted successfully.'}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
            

def download_measure(request, measure_id):
    """
    Télécharge les points de mesure au format CSV pour un DeviceMeasure spécifique.
    """
    # Récupérer les points de mesure pour la mesure spécifiée
    measure_points = db_manager.get_measure_points(measure_id)
    
    # Créer la réponse HTTP avec le bon type de contenu
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="measure_points_{measure_id}.csv"'

    # Créer l'objet CSV writer
    writer = csv.writer(response, delimiter=';')
    
    # Écrire l'en-tête du fichier CSV
    writer.writerow(['timestamp', 'battery', 'integrity', 'sp02', 'bpm', 'obda', 'audio_sp1', 
                     'audio_sp2', 'audio_sp3', 'audio_sp4', 'audio_sp5', 'audio_sp6', 
                     'audio_sp7', 'audio_sp8', 'audio_sp9', 'audio_sp10'])

    # Écrire les données des points de mesure
    for point in measure_points:
        writer.writerow([
            point.timestamp.strftime('%Y-%m-%d %H:%M:%S'),  # Formatage de la date
            point.battery,
            point.integrity,
            point.sp02,
            point.bpm,
            point.obda,
            point.audio_sp1,
            point.audio_sp2,
            point.audio_sp3,
            point.audio_sp4,
            point.audio_sp5,
            point.audio_sp6,
            point.audio_sp7,
            point.audio_sp8,
            point.audio_sp9,
            point.audio_sp10,
        ])

    return response