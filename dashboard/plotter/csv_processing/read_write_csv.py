# Ce fichier contient les fonctions nécessaires à la lecture et à l'écriture des fichiers csv

import pandas as pd
import numpy as np
import io

def normalize_csv_file(filename):
    """
    Réécrit un nouveau csv en supprimant les éventuels ';' à la fin des lignes
    """
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()

    new_filename = filename[:-4] + "_norm" + filename[-4:]
    new_file = open(new_filename, 'w')
    for line in lines:
        if line[0] == ";" or len(line)<2 or not ";" in line:
            continue

        new_file.write(line[:-2])
        if line[-2] != ";":
            new_file.write(line[-2])
        if line[-1] != ";":
            new_file.write(line[-1])
    new_file.close()
    return new_filename


def normalize_csv_buffer(buffer):
    """
    Renvoi un nouveau buffer csv en supprimant les éventuels ';' à la fin des lignes
    """
    lines = buffer.readlines()
    buffer.close()

    new_buffer = io.StringIO()
    for line in lines:
        
        if line[0] == ";" or len(line)<2 or not ";" in line:
            continue

        new_buffer.write(line[:-2])
        if line[-2] != ";":
            new_buffer.write(line[-2])
        if line[-1] != ";":
            new_buffer.write(line[-1])
    
    new_buffer.seek(0)
    return new_buffer


def get_dataframes_from_buffer(buffer):
    """
    Lit un buffer csv et renvoie la liste des dataframes associés à chaque séquence
    """
    # Lecture du fichier csv
    try:
        n_buffer = normalize_csv_buffer(buffer)
        n_buffer.seek(0)
        table = pd.read_csv(n_buffer, header=None, sep=';', skip_blank_lines=True)
    except IOError as e:
        print("Error while reading the csv buffer", e)
        return None

    n_buffer.seek(0)

    print("get_dataframes_from_buffer: buffer normalized")

    # Recherche des différentes séquences dans le fichier
    starts = np.nonzero(np.array(table[0]=='Index'))[0]
    dataframes = []
    for i in range(len(starts)):
        nrows = None
        if i < len(starts)-1:
            nrows = starts[i+1] - starts[i] - 1
        
        try:
            df = pd.read_csv(n_buffer, skiprows=starts[i], sep=';', nrows=nrows, skip_blank_lines=True)
            if df.shape[0] > 0:
                dataframes.append(df)
        except Exception as e:
            print("Error while reading the csv buffer", e)

    #print("get_dataframes_from_buffer: ", dataframes)
    return dataframes


def get_dataframes_from_file(filename):
    """
    Lit le fichier csv et renvoie la liste des dataframes associés à chaque séquence
    """
    
    # Lecture du fichier csv
    try:
        filename = normalize_csv_file(filename)
        table = pd.read_csv(filename, header=None, sep=';', skip_blank_lines=True)
    except:
        print("Error while reading the csv")
        return None

    # Recherche des différentes séquences dans le fichier
    starts = np.nonzero(np.array(table[0]=='Index'))[0]
    dataframes = []
    for i in range(len(starts)):
        nrows = None
        if i < len(starts)-1:
            nrows = starts[i+1] - starts[i] - 1
        
        df = pd.read_csv(filename, skiprows=starts[i], sep=';', nrows=nrows, skip_blank_lines=True)
        if df.shape[0] > 0:
            dataframes.append(df)

    return dataframes


def convert_time_to_sec(time):
    """
    Convertit un string représentant l'heure au format hh:mm:ss 
    en un nombre de secondes
    """
    try:
        values = time.split(":")
        sec = 0
        assert len(values) == 3
    except:
        print("Error in the time format, expected: 'hh:mm:ss', got:", time)
        return time
    
    for i in range(3):
        sec += int(values[i]) * 60**(2-i)
    return sec


def convert_sec_to_time(sec):
    """
    Convertit un nombre de secondes en string représentant l'heure
    au format hh:mm:ss 
    """
    def len_2_str(a):
        st = str(a)
        if len(st)<2:
            st = "0"*(2-len(st)) + st

    s = sec % 60
    m = ((sec % (3600*24)) // 60) % 60
    h = (sec % (3600*24)) // 3600
    
    return len_2_str(h) + ":" + len_2_str(m) + ":" + len_2_str(s)


def get_time_columns(df, columns=None):
    """
    Vérifie l'exploitabilité d'une séquence et renvoie les abscisses en secondes 
    ainsi que le nom des colonnes existantes parmi les colonnes demandées
    """
    if columns is None:
        columns = df.columns[3:]

    try:
        time_axis_seconds = np.array([convert_time_to_sec(time) for time in df["Time"]]).astype('int')

        # On rajoute le nombre de secondes correspondant à une journée entière aux 
        # échantillons dont l'heure est plus petite que celle du premier échantillon
        time_axis_seconds[df["Date"] != df.at[df.index[0], "Date"]] += 3600*24

    except:
        print("Error while trying to read the time and date columns")
        return None

    # Vérification de l'exploitabilité de la séquence
    if df.shape[0] < 10:
        print("Ignoring the sequence because it has less than 10 points")
        return None

    if np.min(time_axis_seconds) == np.max(time_axis_seconds):
        print("Ignoring the sequence because all the data is at the same time sample")
        return None

    average_interval = (np.max(time_axis_seconds) - np.min(time_axis_seconds)) / (len(time_axis_seconds)-1)
    if np.abs(average_interval-2) > 1:
        print("Ignoring the sequence because average time between samples is", average_interval)
        return None

    # Construction de la liste des colonnes du fichier à afficher
    if columns is None:
        columns = df.columns[3:]

    # Liste des colonnes existantes parmi les colonnes demandées en argument
    available_columns = []
    
    for col_name in columns:
        if col_name in df.columns[3:]:
            available_columns.append(col_name)
        else:
            print("No column named", col_name)
            print("Available columns are", list(df.columns))
        
    if len(available_columns) == 0:
        print("Ignoring the sequence because there is no column to plot")
        return None
    
    return time_axis_seconds, available_columns
    

def get_data_type(column_name):
    """
    Renvoie un des identifiants suivants représentant le type de donnée
    en fonction du nom de la colonne
    'CAR' : fréquence cardiaque
    'SAT' : saturation en oxygène
    'ACC' : accélération
    'ROT' : rotation
    'MOV' : donnée de mouvement (combinaison de ACC et ROT)
    'AUD' : volume sonore
    None : autres (température, Unnamed, ...)
    """

    if column_name[:3] == "Car":
        return "CAR"

    if column_name[:3] == "Sat":
        return "SAT"

    if column_name[:3] == "Rot":
        return "ROT"

    if column_name[:3] == "Acc":

        if column_name[-1] == "a":
            return "ROT"

        return "ACC"
    
    if column_name[:3] == "Mov":
        return "MOV"

    if column_name[:3] == "Aud":
        return "AUD"

    if column_name[:3] == "Sou":
        return "AUD"
    
    if column_name[:3] == "Son":
        return "AUD"

    return None


def write_csv(dataframes, filename):
    new_file = open(filename, "w")
    
    for df in dataframes:
        new_file.write(df.to_csv(sep=";", index=False, float_format="%.2f", lineterminator="\n"))
    
    new_file.close()