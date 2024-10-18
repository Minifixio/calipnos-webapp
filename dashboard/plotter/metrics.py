import enum
from enum import Enum

@enum.unique
class Metric(Enum):
    GLOBAL = 'Global'
    SATURATION = 'Saturation(%SpO2)'
    CARDIO = 'Cardio(BPM)'
    AUDIO = 'Audio(%max)'
    MOVEMENT = 'Movement'
    SILENCE = 'Silence'