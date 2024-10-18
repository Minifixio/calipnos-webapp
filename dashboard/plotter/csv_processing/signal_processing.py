# Fichier contenant les différentes fonctions de filtrage des signaux

import numpy as np
from .read_write_csv import *


def remove_outliers(sequence, low_threshold=30, high_threshold=100):
    """
    Détecte les valeurs aberrantes par un simple seuillage
    et les remplace par 0
    """
    clean_sequence = np.copy(sequence)
    clean_sequence[sequence > high_threshold] = 0
    clean_sequence[sequence < low_threshold] = 0

    return clean_sequence


def interpolate_missing_data(sequence):
    """
    Réalise une interpolation linéaire pour remplacer les valeurs manquantes (représentées par 0)
    """
    corrected_sequence = np.copy(sequence)
    ind_zeros = np.nonzero(sequence==0)[0] # Liste des indices des valeurs manquantes

    ind = 0

    while ind < len(ind_zeros):
        start = ind_zeros[ind]
        ind_start = np.copy(ind)

        # On cherche les potentielles valeurs manquantes consécutives
        while ind < len(ind_zeros) and ind_zeros[ind] == ind - ind_start + start: 
            ind += 1

        end = ind_zeros[ind-1] + 1
        
        if start == 0:
            if end < len(sequence):
                corrected_sequence[:end] = sequence[end]
        
        elif end >= len(sequence):
            if start > 0:
                corrected_sequence[start:] = sequence[start-1]

        else:
            # Interpolation linéaire entre la valeur en 'start-1' et la valeur en 'end'
            N = end - start + 1
            t = np.linspace(1/N, 1-1/N, N-1, endpoint=True)
            val_a = sequence[start-1]
            val_b = sequence[end]
            corrected_sequence[start:end] = (1-t)*val_a + t*val_b

    return corrected_sequence


def wiener(sgn, SNR, b, padding_size=None):
    """
    Applique un filtre de Wiener, en supposant que 
    la densité spectrale du bruit est constante, et 
    que le signal utile a la densité spectrale d'un processus
    stationnaire AR(1), de paramètre b.

    Paramètres :
    - sgn : vecteur contenant les échantillons du signal à filtrer
    - SNR : rapport de la puissance du signal utile (après avoir
    enlevé la valeur moyenne) sur la puissance du bruit,
    plus le SNR est faible, plus le bruit est supposé important
    et donc plus le lissage sera important (sur toutes les 
    fréquences de façon uniforme)
    - b : paramètre du modèle du signal utile, il doit être compris 
    entre 0 et 1 strictement, plus il est élevé, plus on considère 
    que le signal est composé uniquement de faibles fréquences, et 
    donc plus les variations rapides seront atténuées
    - padding_size : nombre d'échantillons artificiellement rajoutés
    aux éxtrémités du signal, permet d'aviter les effets de bords 
    liés à la transformée de Fourier. 

    Sortie :
    - Vecteur contenant le signal filtré
    """

    # Taille de l'extension temporelle du vecteur de données
    if padding_size is None:
        padding_size = len(sgn//10)
    
    N = len(sgn)
    N_padded = N + 2*padding_size
    
    # fréquences utilisées pour la transformée de Fourier
    frequencies = np.linspace(0, 1, N_padded, endpoint=False)
    frequencies[frequencies>1/2] -= 1

    # Estimation du niveau de bruit et du signal utile à partir du SNR
    variance = np.var(sgn)
    noise_level = variance / (1 + SNR)
    noise_psd = np.ones(frequencies.size) * noise_level
    noise_psd[0] = 0
    
    signal_level = variance / (1 + 1/SNR)
    signal_psd = signal_level / (1 - np.cos(frequencies*2*np.pi)*2*b + b**2)

    # filtres en fréquences
    wiener_spectral_filter = signal_psd / (signal_psd + noise_psd)

    # extension temporelle du vecteur de données
    padded_signal = np.zeros(N_padded)
    padded_signal[:padding_size] = sgn[0]
    padded_signal[-padding_size:] = sgn[-1]
    padded_signal[padding_size:len(padded_signal)-padding_size] = sgn

    # application du filtre dans le domaine fréquentiel
    fft = np.fft.fft(padded_signal)
    filtered_fft = fft*wiener_spectral_filter
    
    # retour dans le domaine temporel
    padded_correction = np.real(np.fft.ifft(filtered_fft))

    return padded_correction[padding_size:N_padded-padding_size]


def markov(sgn, beta, padding_size=None):
    """
    Estime le signal non déterioré en minisant une énergie correspondant à un modèle markovien
    avec un bruit blanc additif gaussien
    
    Paramètres :
    - sgn : vecteur contenant les échantillons du signal à filtrer
    - beta : paramètre de régularisation, il doit être positif.
    Pour beta = 0, le signal de sortie est identique au signal d'entrée,
    et plus beta est élevé, plus les variations du signal seront atténuées
    - padding_size : nombre d'échantillons artificiellement rajoutés
    aux éxtrémités du signal, permet d'aviter les effets de bords 
    liés à la transformée de Fourier. 

    Sortie :
    - Vecteur contenant le signal filtré
    """
    # Taille de l'extension temporelle du vecteur de données
    if padding_size is None:
        padding_size = len(sgn//10)
    
    N = len(sgn)
    N_padded = N + 2*padding_size
    
    # extension temporelle du vecteur de données
    padded_signal = np.zeros(N_padded)
    padded_signal[:padding_size] = sgn[0]
    padded_signal[-padding_size:] = sgn[-1]
    padded_signal[padding_size:len(padded_signal)-padding_size] = sgn

    # noyau de convolution de la dérivée
    time_derivative = np.zeros(N_padded)
    time_derivative[0] = 1
    time_derivative[1] = -1

    # filtrage dans le domaine fréquentiel
    fft = np.fft.fft(padded_signal)
    fft_der = np.fft.fft(time_derivative)

    filtered_fft = fft / (1 + beta*np.abs(fft_der)**2)

    # retour dans le domaine temporel
    padded_correction = np.real(np.fft.ifft(filtered_fft))

    return padded_correction[padding_size:N_padded-padding_size]


def median_filter(sgn, window_size=11):
    """
    Renvoie le signal lissé par un filtre médian, c'est-à-dire que l'on remplace 
    chaque échantillon par la médiane des valeurs présentes dans une fenêtre de taille
    'window_size' (impaire) centrée sur cet échantillon
    """
    N = len(sgn)
    np_sgn = np.array(sgn)
    
    filtered_signal = np.zeros(N)
    for i in range(N):
        window = np_sgn[max(0, i-window_size//2): min(N, i+1+window_size//2)]
        filtered_signal[i] = np.median(window)

    return filtered_signal


def movement_detection(rotation, acceleration, threshold=1, eps=1e-3, scale=1):
    """
    Prend en entrée les données de rotation et d'accélération et les combine en une
    unique donnée de mouvement
    """
    
    # Normalisation des données de rotation
    rot_norm = rotation - np.median(rotation)
    quartile = np.quantile(np.abs(rot_norm), 0.75)
    max_abs = np.max(np.abs(rot_norm))

    if quartile != 0 :
        rot_norm /= quartile

    elif max_abs != 0 :
        rot_norm /= max_abs
    
    
    # Normalisation des données d'accélération
    acc_norm = acceleration - np.median(acceleration)
    quartile = np.quantile(np.abs(acc_norm), 0.75)
    max_abs = np.max(np.abs(acc_norm))
    
    if quartile != 0 :
        acc_norm /= quartile

    elif max_abs != 0 :
        acc_norm /= max_abs


    # Combinaison de la rotation et de l'accélération
    movement = np.sqrt(rot_norm**2 + acc_norm**2)

    # Tranformation logarithmique
    movement = np.log(eps + scale*movement)

    # Applique un seuillage
    movement[movement>threshold] = threshold

    return movement 


def std_window(sgn, window_size=9, use_mask=False):
    """
    Renvoie l'évolution de l'écart-type local du signal, c'est-à-dire que l'on remplace 
    chaque échantillon par l'écart-type des valeurs présentes dans une fenêtre de taille
    'window_size' (impaire) centrée sur cet échantillon
    """
    N = len(sgn)
    np_sgn = np.array(sgn)

    if use_mask:
        mask = np.hanning(window_size)
    
    std = np.zeros(N)
    for i in range(N):
        window = np_sgn[max(0, i-window_size//2): min(N, i+1+window_size//2)]

        if use_mask:
            if len(window) == window_size:
                std[i] = np.std((window-np.mean(window))*mask)
            
            else:
                std[i] = np.std((window-np.mean(window))*np.hanning(len(window)))

        else:
            std[i] = np.std(window)

    return std


def find_threshold_scale(sgn, q=0.1, threshold_fact=4, scale_fact=1):
    """
    Détermine le seuil et l'échelle utilisés pour la détection d'événements, 
    en fonction du quantile 'q' de la distribution des valeurs du signal
    """
    
    q1 = np.quantile(sgn, q)
    m = np.min(sgn)

    threshold = m + (q1-m)*threshold_fact

    if q1 != m:
        scale = scale_fact / (q1-m)
    
    else:
        M = np.max(sgn)
        if M != m:
            scale = scale_fact / (q*(M-m))

        else:
            # si le signal est constant
            return None 

    return threshold, scale


def event_detection(sgn, data_type, event_det_params):
    """
    Prend en entrée un signal sur lequel on souhaite faire une détection d'événements,
    puis calcule un écart-type local, et en déduit un signal de détection d'événements
    compris entre 0 et 1 pour chaque échantillon de temps.
    """

    local_std = std_window(sgn, window_size=event_det_params["window_size"],
                            use_mask=True)

    # détermine les bons paramètres en fonction du type de signal
    try:
        threshold_scale = find_threshold_scale(local_std, q=event_det_params[data_type + "_q"], 
                                                threshold_fact=event_det_params[data_type + "_threshold_fact"], 
                                                scale_fact=event_det_params[data_type + "_scale_fact"])
        
    except:
        threshold_scale = find_threshold_scale(local_std, data_type)

    if threshold_scale is None:
        # dans le cas où le signal est constant 
        # il n'y a pas d'événement
        return np.zeros(len(sgn))
    
    # application de la transformation affine 
    threshold, scale = threshold_scale
    scaled_std = scale*(local_std-threshold)

    # application de la sigmoïde
    event_detector = 1 / (1 + np.exp(-scaled_std))

    return event_detector


def combine_detections(detections):
    """
    Prend en entrée un dictionnaire contenant des données de détection d'évenements 
    sur différents signaux, et les combine en un seul signal de détéction d'évenement global
    """
    N = 0
    global_detection = None

    for key in detections:
        if N == 0:
            global_detection = np.ones(len(detections[key]))
        
        detect = detections[key]
        if get_data_type(key) == "AUD":
            detect = 1 - detect
        global_detection *= detect

        N += 1

    return global_detection