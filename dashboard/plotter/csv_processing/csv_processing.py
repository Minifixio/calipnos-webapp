# Fichier contenant les différentes fonctions permettant l'exploitation des données lues dans les csv

# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import os

from .signal_processing import *
from .read_write_csv import *


def extract_relevant_parts(sequence, min_length=15, max_missing_data_length=10):
    """
    Extrait les portions du signal exploitables, c'est-à-dire 
    ne contenant pas plus de 'max_missing_data_length' valeurs manquantes consécutives, 
    et d'une longueur minimale de 'min_length'
    Renvoie la liste des couples (start, end) correspondant à chaque portion exploitable
    (La borne supérieure 'end' est exclue de chaque portion)
    """
    nz = np.nonzero(sequence)[0] # liste des indices des valeurs non nulles

    parts = [] # liste des couples (start, end) de chaque séquence

    ind = 0

    while ind + 1 < len(nz):
        start = nz[ind]
        while nz[ind+1] - nz[ind] < max_missing_data_length: 
            # tant que le nombres de données manquantes consécutives est inférieur au seuil fixé
            if ind + 2 < len(nz):
                ind += 1

            else:
                break

        end = nz[ind] + 1
        if end - start > min_length:
            # si la portion du signal est suffisamment longue
            parts.append((start, end))

        ind += 1
    
    return parts


def intersection_of_segments(parts_A, parts_B, length_min=10):
    """
    Cherche les parties exploitables à la fois pour la colonne A et pour la colonne B

    Entrée :
    - parts_A : liste des couples (start, end) représentant les parties exploitables de la colonne A
    - parts_B : liste des couples (start, end) représentant les parties exploitables de la colonne B
    - length_min : flottant ou entier positif, longueur minimale d'une intersection pour être sauvegardée

    Sortie :
    - intersecting_parts : liste des couples (start, end) représentant les parties exploitables 
    pour les deux colonnes en même temps
    """

    intersecting_parts = [] # Liste des intersections
    j = 0
        
    for i in range(len(parts_A)):
        # Pour chaque partie de la liste A, on cherche les intersections avec 
        # les parties de la liste B

        while j < len(parts_B) and parts_B[j][0] < parts_A[i][1]:
            start = max(parts_A[i][0], parts_B[j][0])
            end = min(parts_A[i][1], parts_B[j][1])

            if end - start > length_min: 
                # On ajoute l'intersection si elle est suffisament longue
                intersecting_parts.append((start, end))
            j += 1

    return intersecting_parts


def filter_part(dataframe, filter_params):
    """
    Applique un premier traitement à une partie exploitable de la séquence.
    Pour les données de rythme cardiaque et de saturation, les valeurs manquantes ou
    aberrantes sont remplacées par interpolation linéaire,
    les colonnes accélération et rotation sont remplacées par une colonne de mouvement,
    la colonne d'intensité sonore est laissée identique.

    Ces différentes colonnes sont stockées dans le dataframe 'prefiltered', et la 
    fonction renvoie également 'filtered' qui contient les données de rythme
    cardiaque et de saturation après filtrage.

    Les paramètres par défaut de la fonction définissent les seuils respectifs pour le 
    rythme cardiaque et la saturation en oxygène pour la suppression des valeurs aberrantes
    """

    prefiltered = dataframe.copy()
    filtered = pd.DataFrame(index=dataframe.index)
    return_tuple = get_time_columns(dataframe)

    if return_tuple is None:
        return None

    time_axis_seconds, available_columns = return_tuple

    rotation_column = None
    acceleration_column = None

    for col_name in available_columns:
        data_type = get_data_type(col_name)

        if data_type == "CAR":
            # Traitement du rythme cardiaque
            # Suppresion des valeurs aberantes
            corrected_part = remove_outliers(prefiltered[col_name], 
                                             low_threshold=filter_params["cardio_low_threshold"],
                                             high_threshold=filter_params["cardio_high_threshold"])

            # Interpolation linéaire pour les valeurs manquantes
            corrected_part = interpolate_missing_data(corrected_part)

            # Stockage du signal préfiltré et de la détection d'évenements dans le dictionnaire
            prefiltered[col_name] = corrected_part

            # Filtrage de Wiener
            filtered[col_name] = wiener(corrected_part, SNR=filter_params["wiener_SNR"], 
                                           b=filter_params["wiener_b"])


        elif data_type == "SAT":
            # Traitement de la saturation en oxygène
            # Suppresion des valeurs abberantes
            corrected_part = remove_outliers(prefiltered[col_name], 
                                                low_threshold=filter_params["spO2_low_threshold"],
                                                high_threshold=filter_params["spO2_high_threshold"])

            # Interpolation linéaire pour les valeurs manquantes
            corrected_part = interpolate_missing_data(corrected_part)

            # Stockage du signal préfiltré et de la détection d'évenements dans le dictionnaire
            prefiltered[col_name] = corrected_part

            # Filtrage par modèle Markovien
            filtered[col_name] = markov(corrected_part, beta=filter_params["markov_beta"])

        elif data_type == "ROT":
            rotation_column = col_name
            prefiltered.drop(labels=col_name, axis=1, inplace=True)

        elif data_type == "ACC":
            acceleration_column = col_name
            prefiltered.drop(labels=col_name, axis=1, inplace=True)
        
        elif data_type == "AUD":
            prefiltered[col_name] = dataframe[col_name]

        else:
            prefiltered.drop(labels=col_name, axis=1, inplace=True)

    # Ecriture de la colonne de détection de mouvement
    if rotation_column is not None and acceleration_column is not None:
        # Filter the acceleration
        acceleration = dataframe[acceleration_column] - median_filter(dataframe[acceleration_column])
        prefiltered["Movement"] = movement_detection(dataframe[rotation_column],
                                                          acceleration,
                                                          threshold=1, eps=1, scale=0.1)
       
    return prefiltered, filtered


def process_part(dataframe, filter_params, event_det_params, enable_event_detection=True, plot=False):
    """
    Traite une partie exploitable d'une séquence en combinant les données filtrées et 
    préfiltrées en fonction de la détection d'événements.
    """

    prefiltered, filtered = filter_part(dataframe, filter_params)

    time_axis_seconds, available_columns = get_time_columns(prefiltered)

    # Détection d'évenements sur l'ensemble des signaux préfiltrés
    event_detections = {}
    for col_name in available_columns:
        event_detections[col_name] = event_detection(prefiltered[col_name], 
                                                        get_data_type(col_name), 
                                                        event_det_params)

    # Combinaison des détections d'événements
    if enable_event_detection:
        global_events = combine_detections(event_detections)
    else:        
        global_events = np.zeros(filtered.shape[0])

    non_events = 1 - global_events

    # Création du dataframe final
    new_dataframe = prefiltered.copy()

    for col_name in available_columns:
        data_type = get_data_type(col_name)

        if data_type == "CAR" or data_type == "SAT":
            # Filtrage lorsqu'il n'y a pas d'événements
            new_dataframe[col_name] += non_events * (filtered[col_name]-prefiltered[col_name])

        elif data_type == "AUD":
            new_dataframe["Silence"] = 1-event_detections[col_name]
        
    new_dataframe["Global"] = global_events

    return new_dataframe
    

def process_dataframe(dataframe, filter_params, event_det_params,
                      event_detection=True, plot=False):
    """
    Prend en entrée un dataframe correspondant à une séquence d'un fichier csv,
    sépare cette séquence en différentes parties exploitables,
    applique 'process_part' sur chaque partie exploitable,
    et enfin renvoie une liste de dataframes représentant chaque partie exploitable après traitement
    """

    # Extraction des parties exploitables

    # Liste des listes de parties exploitables des colonnes de fréquence cardiaque et de saturation
    # (il y a potentiellement plusieurs colonnes de chaque type)
    relevant_parts_lists = [] 

    for col_name in dataframe.columns:
        if col_name[:3] == "Car" or col_name[:3] == "Sat":
            # Extraction des parties exploitables pour cette colonne
            data_col = np.array(dataframe[col_name])
            relevant_parts_lists.append(extract_relevant_parts(data_col))
    
    if len(relevant_parts_lists) == 0:
        print("No exploitable data in the sequence")
        return None

    # Calcul itératif des intersections de toutes les parties exploitables
    relevant_parts = relevant_parts_lists[0] # Contient la liste des parties exploitables pour toutes les colonnes

    for parts in relevant_parts_lists[1:]:
        relevant_parts = intersection_of_segments(relevant_parts, parts)
    
    if len(relevant_parts) == 0:
        print("No relevant parts in the sequence")
        return None   

    # Liste des dataframes pour chaque partie exploitable
    dataframes = []
    for (start, end) in relevant_parts:
        df_part = dataframe.iloc[start:end]
        df_part = process_part(df_part, filter_params, event_det_params, 
                               plot=plot, enable_event_detection=event_detection)

        if df_part is not None:
            dataframes.append(df_part)

    return dataframes

def process_csv_file(source_filename, target_filename, filter_params, 
                event_det_params, event_detection=True, plot=False):
    """
    Lit les différentes séquences du fichier csv 'source_filename', 
    puis utilise 'process_dataframe' pour extraire les parties exploitables
    et leur appliquer le traitement adapté,
    enfin, les nouvelles séquences obtenues sont écrites dans le fichier 
    'target_filename'
    - 'event_detection' permet d'atténuer le lissage lorsque des évévements sont détéctées
    simultanément sur les différentes données
    - 'plot' permet l'affichage graphique des différentes données avec matplotlib
    """
    print("\nProcess file", source_filename)
    dataframes = get_dataframes_from_file(source_filename)

    if dataframes is None:
        return None

    dataframes_to_write = [] # Liste des séquences traitées à écrire dans le nouveau fichier

    for i in range(len(dataframes)):
        
            # Traitement de la séquence à afficher
            df = dataframes[i]
            try:
                print("\nSequence number", i, "(starts at", df.at[0, "Time"], 
                "ends at", str(df.at[df.shape[0]-1, "Time"]) + ")")
            except:
                print("Error with the indexes")
                print(df.index)
            
            return_tuple = get_time_columns(df, None)

            if return_tuple is None:
                # La séquence n'est pas exploitable
                continue

            # Traitement de chaque partie exploitable de la séquence
            parts_dfs = process_dataframe(df, filter_params, event_det_params,
                                          plot=plot, event_detection=event_detection) # Liste des dataframes de chaque partie exploitable

            if parts_dfs is not None:
                dataframes_to_write.extend(parts_dfs)
            
    if len(dataframes_to_write) > 0:
        write_csv(dataframes_to_write, target_filename)
        print("\nCleaned was data written in", target_filename)
    
    else:
        print("\n", target_filename, "was not created because there is no usable part in the source file.")


def process_csv_buffer(buffer, filter_params, 
                event_det_params, event_detection=True, plot=False):
    """
    Lit les différentes séquences du fichier csv 'source_filename', 
    puis utilise 'process_dataframe' pour extraire les parties exploitables
    et leur appliquer le traitement adapté,
    enfin, les nouvelles séquences obtenues sont écrites dans le fichier 
    'target_filename'
    - 'event_detection' permet d'atténuer le lissage lorsque des évévements sont détéctées
    simultanément sur les différentes données
    - 'plot' permet l'affichage graphique des différentes données avec matplotlib
    """
    print("\nProcess buffer")
    dataframes = get_dataframes_from_buffer(buffer)
    print("\nData frames acquired :", dataframes)

    if dataframes is None:
        return None

    dataframes_to_return = [] # Liste des séquences traitées à écrire dans le nouveau fichier

    for i in range(len(dataframes)):
        
            # Traitement de la séquence à afficher
            df = dataframes[i]
            try:
                print("\nSequence number", i, "(starts at", df.at[0, "Time"], 
                "ends at", str(df.at[df.shape[0]-1, "Time"]) + ")")
            except:
                print("Error with the indexes")
                print(df.index)
            
            return_tuple = get_time_columns(df, None)

            if return_tuple is None:
                # La séquence n'est pas exploitable
                continue
            
            # Traitement de chaque partie exploitable de la séquence
            parts_dfs = process_dataframe(df, filter_params, event_det_params,
                                          plot=plot, event_detection=event_detection) # Liste des dataframes de chaque partie exploitable
            if parts_dfs is not None:
                dataframes_to_return.extend(parts_dfs)
            
    if len(dataframes_to_return) > 0:
        return dataframes_to_return
    else:
        print("\n", "Error while processing the buffer : there is no usable part in the source buffer.")


def process_folder(source_folder, target_folder, filter_params, 
                   event_det_params, event_detection=True, plot=False):
    """
    Traite les fichiers csv présents dans le dossier 'source_folder', 
    et crée pour chacun un fichier du même nom dans le dossier
    'target_folder'
    - 'event_detection' permet d'atténuer le lissage lorsque des évévements sont détéctés
    simultanément sur les différentes données
    """
    files = os.listdir(source_folder)
    source_paths = []
    target_paths = []
    for file in files:
        if len(file) < 4:
            continue
        
        if len(file) > 9 and file[-9:-4] == "_norm":
            continue

        if file[-4:] == ".csv" or file[-4:] == ".CSV":
            source_paths.append(source_folder + "/" + file)
            target_paths.append(target_folder + "/" + file)

    print("Found {} files in the folder '{}'".format(len(source_paths), source_folder))

    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print("Target folder '{}' was created".format(target_folder))
    
    for (i, source_filename) in enumerate(source_paths):
        print("\nFile {}/{}".format(i+1, len(source_paths)))
        process_csv_file(source_filename, target_paths[i],  filter_params, 
                   event_det_params, plot=plot, event_detection=event_detection)
    
    print("\nAll the files were processed, you can find the results in the folder '{}'".format(target_folder))

