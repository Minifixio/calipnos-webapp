from functools import reduce
from ..binary_utils import read as binary_read
from client.models import ConfigurationPairings, DeviceConfiguration, DeviceConfigurationParameterName, DeviceConfigurationParameterValue, DeviceMeasure, DeviceMeasurePoint, DoctorConfiguration, DoctorConfigurationParameterName, DoctorConfigurationParameterValue
import datetime
import pytz
from django.db.models import Q, Count, Max

def convert_ms_to_datetime(seconds):
    # Convertir le timestamp en objet datetime
    date_time = datetime.datetime.fromtimestamp(seconds, tz=pytz.utc)
    return date_time

def add_measure(file_content):
    """
    Ajoute une nouvelle mesure à la base de données en parsant le contenu du fichier binaire.
    """
    # TODO: Ajouter la gestion d'erreurs de lecture binaires
    result = binary_read.read_binary_file(file_content)
    
    # Le format du résultat est le suivant:
    # result = {
    #     'timestamp_start': timestamp_start,
    #     'timestamp_stop': timestamp_stop,
    #     'version': version,
    #     'pta': pta,
    #     'measures': measures,
    #     'config': config,
    # }

    measure = DeviceMeasure(
        version=result['version'],
        config=result['config'],
        pta=result['pta'],
        start_time=convert_ms_to_datetime(result['timestamp_start']),
        end_time=convert_ms_to_datetime(result['timestamp_stop']),
        points_count=len(result['measures'])
    )
    measure.save()
    print(f"Saved measure with ID: {measure.id}")

    # Le format des mesures est le suivant:
    # measure = {
    #     timestamp,
    #     battery,
    #     integrity,
    #     spo2,
    #     heart_rate,
    #     odba,
    #     audio_sp1,
    #     audio_sp2,
    #     audio_sp3,
    #     audio_sp4,
    #     audio_sp5,
    #     audio_sp6,
    #     audio_sp7,
    #     audio_sp8,
    #     audio_sp9,
    #     audio_sp10
    # }

    for m in result['measures']:
        measure_point = DeviceMeasurePoint(
            measure=measure,
            timestamp=convert_ms_to_datetime(m['timestamp']),
            battery=m['battery'],
            integrity=m['integrity'],
            sp02=m['spo2'],
            bpm=m['heart_rate'],
            obda=m['odba'],
            audio_sp1=m['audio_sp1'],
            audio_sp2=m['audio_sp2'],
            audio_sp3=m['audio_sp3'],
            audio_sp4=m['audio_sp4'],
            audio_sp5=m['audio_sp5'],
            audio_sp6=m['audio_sp6'],
            audio_sp7=m['audio_sp7'],
            audio_sp8=m['audio_sp8'],
            audio_sp9=m['audio_sp9'],
            audio_sp10=m['audio_sp10']
        )
        measure_point.save()
    
    print(f"Saved {len(result['measures'])} measure points")

def get_measures():
    """
    Récupère toutes les mesures de la base de données.
    """
    measures = DeviceMeasure.objects.all()
    return measures

def get_measure(measure_id):
    """
    Récupère une mesure spécifique de la base de données.
    """
    try:
        measure = DeviceMeasure.objects.get(id=measure_id)
        return measure
    except DeviceMeasure.DoesNotExist:
        print("Trying to get a non-existing measure")
        return None
    
def delete_measure(measure_id):
    """
    Supprime une mesure de la base de données.
    """
    try:
        measure = DeviceMeasure.objects.get(id=measure_id)
        measure.delete()
        
        # Supprimer les points de mesure associés
        # TODO: Check si nécessaire
        measure_points = DeviceMeasurePoint.objects.filter(measure=measure)
        for point in measure_points:
            point.delete()
        return True
    except DeviceMeasure.DoesNotExist:
        print("Trying to delete a non-existing measure")
        return False
    
def get_measure_points(measure_id):
    """
    Récupère les points de mesure pour une mesure spécifique.
    """
    try:
        measure = DeviceMeasure.objects.get(id=measure_id)
        measure_points = DeviceMeasurePoint.objects.filter(measure=measure)
        return measure_points
    except DeviceMeasurePoint.DoesNotExist:
        print("Trying to get points for a non-existing measure")
        return None
    
def get_doctor_configurations():
        # Récupére les noms des paramètres depuis DoctorConfigurationParameterName
        # Pour chaque paramètre param_n, on récupére les valeurs des paramètres 
        # depuis DoctorConfigurationParameterValue pour lesquels param=param_n

        params_with_values = list()

        # Récupérer tous les paramètres
        parameters = DoctorConfigurationParameterName.objects.all()

        for param in parameters:
            # Récupérer les valeurs distinctes pour chaque paramètre
            values = list(DoctorConfigurationParameterValue.objects.filter(param=param).values('id', 'value').distinct())

            # Ajouter au dictionnaire
            params_with_values.append({
                'param': param,
                'values': values
            })
        
        return params_with_values

def get_device_configurations():
    # Récupére les noms des paramètres depuis DeviceConfigurationParameterName
    # Pour chaque paramètre param_n, on récupére les valeurs des paramètres 
    # depuis DeviceConfigurationParameterValue pour lesquels param=param_n

    params_with_values = list()

    # Récupérer tous les paramètres
    parameters = DeviceConfigurationParameterName.objects.all()

    for param in parameters:
        # Récupérer les valeurs distinctes pour chaque paramètre
        values = DeviceConfigurationParameterValue.objects.filter(param=param).values('id', 'value').distinct()

        # Ajouter au dictionnaire
        params_with_values.append({
            param: param,
            values: values
        })
    
    return dict(params_with_values)

def get_device_configurations_selection():
    parameters = DeviceConfigurationParameterName.objects.all()
    return parameters

def update_configuration_rule(doctor_config, device_config):
    """ Mettre à jour les configurations pour un médecin et un appareil spécifiques
    
    Parameters
    ----------
    doctor_config : dict
        De la forme : {'param1': 'value1', 'param2': 'value2', ...}
    
    device_config : dict
        De la forme : {'param1': 'value1', 'param2': 'value2', ...}
    """

    queries_doctor = []

    for param_id, value_id in doctor_config.items():
        # Chaque condition pour le paramètre et sa valeur
        queries_doctor.append(Q(param__id=param_id) & Q(value__id=value_id))

    # Regrouper toutes les requêtes avec un OR
    # Puis filtrer sur les config_id qui ont toutes les conditions
    results_doctor = DoctorConfiguration.objects.filter(
        reduce(lambda x, y: x | y, queries_doctor)
    ).values('config_id').annotate(param_count=Count('param')).order_by().distinct()

    # Uniquement les config_id qui correspondent au nombre de paramètres
    valid_doctor_config_ids = [
        config['config_id'] for config in results_doctor if config['param_count'] == len(doctor_config)
    ]

    # Utilise le premier config_id valide
    doctor_config_id = None
    if len(valid_doctor_config_ids) > 0:
        print("Found valid doctor config")
        doctor_config_id = valid_doctor_config_ids[0]
    else:
        print("Creating new doctor config")
        # Créer une nouvelle configuration en récupérant le config_id max et en l'incrémentant de 1
        max_config_id = DoctorConfiguration.objects.aggregate(Max('config_id'))['config_id__max']
        if max_config_id is None:
            doctor_config_id = 1
        else:
            doctor_config_id = max_config_id + 1

        print(doctor_config_id)

        # Ajouter les paramètres et valeurs
        for param_id, value_id in doctor_config.items():
            DoctorConfiguration.objects.create(
                config_id=doctor_config_id,
                param_id=param_id,
                value_id=value_id
            )
            
        
    # Pour chacune des clé name, value de device_config,
    # reagarder si il existe une entrée dans DeviceConfigurationParameterValue avec le même name et value
    # Si non, la créer
    for param_id, param_value in device_config.items():
        # Vérifier si le paramètre existe
        param = DeviceConfigurationParameterName.objects.get(id=param_id)

        # Vérifier si la valeur existe
        value = DeviceConfigurationParameterValue.objects.filter(param=param, value=param_value)
        if not value.exists():
            DeviceConfigurationParameterValue.objects.create(param=param, value=param_value)

    # Mettre à jour la configuration de l'appareil
    queries_device = []

    for param_id, value_id in device_config.items():
        # Chaque condition pour le paramètre et sa valeur
        queries_device.append(Q(param__id=param_id) & Q(value__id=value_id))

    # Regrouper toutes les requêtes avec un OR
    # Filtrer sur les config_id qui ont toutes les conditions
    results_device = DoctorConfiguration.objects.filter(
        reduce(lambda x, y: x | y, queries_device)
    ).values('config_id').annotate(param_count=Count('param')).order_by().distinct()

    # Uniquement les config_id qui correspondent au nombre de paramètres
    valid_device_config_ids = [
        config['config_id'] for config in results_device if config['param_count'] == len(device_config)
    ]

    # Utilise le premier config_id valide
    device_config_id = None
    if len(valid_device_config_ids) > 0:
        print("Found valid device config")
        device_config_id = valid_device_config_ids[0]
    else:
        print("Creating new device config")
        # Créer une nouvelle configuration en récupérant le config_id max et en l'incrémentant de 1
        max_config_id = DeviceConfiguration.objects.aggregate(Max('config_id'))['config_id__max']
        if max_config_id is None:
            device_config_id = 1
        else:
            device_config_id = max_config_id + 1

        # Ajouter les paramètres et valeurs
        for param_id, param_value in device_config.items():
            # On récupère le param avec l'id param_id
            param = DeviceConfigurationParameterName.objects.get(id=param_id)

            # On récupère la value avec param = param et value = param_value
            value = DeviceConfigurationParameterValue.objects.get(param=param, value=param_value)

            DeviceConfiguration.objects.create(
                config_id=device_config_id,
                param=param,
                value=value
            )

    
    # Regarder si il existe déjà une association entre les deux configurations
    # Si oui, on la met à jour, sinon on en crée une nouvelle
    pairing_both = ConfigurationPairings.objects.filter(doctor_config_id=doctor_config_id, device_config_id=device_config_id)
    pairing_doctor = ConfigurationPairings.objects.filter(doctor_config_id=doctor_config_id)
    pairing_device = ConfigurationPairings.objects.filter(device_config_id=device_config_id)

    if len(pairing_both) > 0:
        print("Updating both")
        pairing_both.update(doctor_config_id=doctor_config_id, device_config_id=device_config_id)
    elif len(pairing_doctor) > 0:
        print("Updating doctor")
        pairing_doctor.update(doctor_config_id=doctor_config_id, device_config_id=device_config_id)
    elif len(pairing_device) > 0:
        print("Updating device")
        pairing_device.update(doctor_config_id=doctor_config_id, device_config_id=device_config_id)
    else:
        print("Creating new pairing")
        ConfigurationPairings.objects.create(doctor_config_id=doctor_config_id, device_config_id=device_config_id)

    return

def get_device_configuration_from_doctor_configuration(doctor_config):
    """
    Récupère la configuration de l'appareil à partir de la configuration du médecin.
    """
    
    queries_doctor = []

    for param_id, value_id in doctor_config.items():
        # Chaque condition pour le paramètre et sa valeur
        queries_doctor.append(Q(param__id=param_id) & Q(value__id=value_id))

    # Regrouper toutes les requêtes avec un OR
    # Puis filtrer sur les config_id qui ont toutes les conditions
    results_doctor = DoctorConfiguration.objects.filter(
        reduce(lambda x, y: x | y, queries_doctor)
    ).values('config_id').annotate(param_count=Count('param')).order_by().distinct()

    # Uniquement les config_id qui correspondent au nombre de paramètres
    valid_doctor_config_ids = [
        config['config_id'] for config in results_doctor if config['param_count'] == len(doctor_config)
    ]

    # Utilise le premier config_id valide
    doctor_config_id = None
    if len(valid_doctor_config_ids) > 0:
        print("Found valid doctor config")
        doctor_config_id = valid_doctor_config_ids[0]
    else:
        return None
    
    # Récupérer la configuration de l'appareil associée
    try:
        pairing = ConfigurationPairings.objects.get(doctor_config_id=doctor_config_id)
        device_config_id = pairing.device_config_id
        configurations = DeviceConfiguration.objects.filter(config_id=device_config_id)

        result = [
            {
                config.param.name: config.value.value
            }
            for config in configurations
        ]

        return result
    except ConfigurationPairings.DoesNotExist:
        return None
    
def get_configuration_pairings():
    """
    Récupère toutes les associations entre les configurations du médecin et de l'appareil.
    """
    pairings = ConfigurationPairings.objects.all()
    
    # Récupérer les configurations sous forme liste de dictionnaires nom-valeur
    result = []
    for pairing in pairings:
        doctor_config_id = pairing.doctor_config_id
        device_config_id = pairing.device_config_id
        
        doctor_config = DoctorConfiguration.objects.filter(config_id=doctor_config_id)
        device_config = DeviceConfiguration.objects.filter(config_id=device_config_id)
        
        doctor_config_dict = {
            config.param.name: config.value.value
            for config in doctor_config
        }
        
        device_config_dict = {
            config.param.name: config.value.value
            for config in device_config
        }
        
        result.append({
            'doctor_config': doctor_config_dict,
            'device_config': device_config_dict
        })

    return result