## Démarrer l'environnement de test :
L’application est compatible Python 3.8 et Python 3.9. La version sur PythonAnywhere est 3.9.

Pour développer en local, il est nécessaire d’installer les librairies sur lesquelles dépend le projet. Ces dernières sont listées dans le fichier `/dashboard/requirements.txt``.

Pour les installer, vous pouvez soit le faire directement sur votre poste avec pip :
```bash
$ pip install -r requirements.txt
```

ou alors en utilisant un environnement python virtuel (venv) situé à la racine
```bash
$ pip install virtualenv
$ python -m venv myvenv
$ source myvenv/bin/activate 
```

Ensuite il suffit de se rendre dans le répertoire `/dashboard` et de faire : 
```bash
$ python manage.py runserver
```

L’application locale sera disponible à l’adresse http://127.0.0.1:8000/

## Paramètres pouvant être modifiés sur l'interface (et leur valeur par défaut)
### Filtrage de la saturation
- "spO2_low_threshold": 80,
- "spO2_high_threshold": 100

### Filtrage de la fréquence cardiaque
- "cardio_low_threshold": 40
- "cardio_high_threshold": 120

### Taille de la fenêtre glissante
- "window_size": 9

## Notes de développement
- La section "Evenement" en sortie du script de traitement des fichiers csv correspond à la métrique "Global"
- Les noms des colonnes ne doivent pas se répéter dans le fichier csv (i.e il doit y avoir une seule en tête et elle doit être au début du fichier)

