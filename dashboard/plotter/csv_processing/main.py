# Fichier principal à éxécuter pour traiter les fichiers csv

import csv_processing as cp


### Définition des paramètres

filter_params = { 
    # paramètres de filtrage des données
    # filtrage de la saturation
    "spO2_low_threshold": 80, 
    "spO2_high_threshold": 100,
    "markov_beta": 5,

    # filtrage de la fréquence cardiaque
    "cardio_low_threshold": 40,
    "cardio_high_threshold": 120,
    "wiener_b": 0.8,
    "wiener_SNR": 0.2
                }

event_det_params = { 
    # paramètres de détection d'événements
    # taille de la fenêtre glissante
    "window_size": 9,

    # données de fréquence cardiaque
    "CAR_q": 0.1, 
    "CAR_threshold_fact": 4, 
    "CAR_scale_fact": 1,

    # données de saturation 
    "SAT_q": 0.3, 
    "SAT_threshold_fact": 4, 
    "SAT_scale_fact": 2,

    # données de mouvement 
    "MOV_q": 0.2, 
    "MOV_threshold_fact": 4, 
    "MOV_scale_fact": 1,

    # données de son 
    "AUD_q": 0.1, 
    "AUD_threshold_fact": 2, 
    "AUD_scale_fact": 1,
                }


### Exemple de traitement d'un fichier csv unique
source_filename = "../2023_04_10-11_Emmanuel.csv" # Chemin relatif vers un fichier csv à traiter
target_filename = "../2023_04_10-11_Emmanuel_cleaned_data.csv" # Chemin relatif vers le fichier d'écriture

cp.process_csv_file(source_filename, target_filename, filter_params, 
               event_det_params, plot=False, event_detection=True)



### Exemple de traitement de tous les fichiers d'un dossier
'''
source_folder = "../Data" # Chemin relatif vers le dossier contenant les csv à traiter
target_folder = "../Output" # Chemin relatif vers le dossier d'écriture des csv

cp.process_folder(source_folder, target_folder, filter_params, 
                  event_det_params)
'''

