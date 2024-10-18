

class AppConstants:
    DEBUG_MODE = True
    DEBUG_FILE = "2023_04_10-11_Emmanuel.csv"

class ProcessingConstants:
    DEFAULT_FILTER_PARAMS = { 
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

    DEFAULT_EVENT_DET_PARAMS = { 
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
