instagram_etl_project/
│
├── config/
│   ├── __init__.py
│   ├── database_config.py          # Configuration base de données
│   ├── instagram_config.py         # Configuration API Instagram
│   └── model_config.py             # Configuration modèles ML
│
├── src/
│   ├── __init__.py
│   │
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── instagram_extractor.py  # Extraction données Instagram
│   │   └── api_utils.py            # Utilitaires API
│   │
│   ├── transformation/
│   │   ├── __init__.py
│   │   ├── data_cleaner.py         # Nettoyage des données
│   │   ├── text_processor.py       # Traitement du texte
│   │   └── data_validator.py       # Validation des données
│   │
│   ├── loading/
│   │   ├── __init__.py
│   │   ├── database_loader.py      # Chargement en base
│   │   └── sql_queries.py          # Requêtes SQL
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── sentiment_analyzer.py   # Analyseur de sentiment
│   │   ├── model_trainer.py        # Entraînement modèles
│   │   └── model_evaluator.py      # Évaluation modèles
│   │
│   └── dashboard/
│       ├── __init__.py
│       ├── powerbi_connector.py    # Connecteur Power BI
│       └── data_aggregator.py      # Agrégation données
│
├── data/
│   ├── raw/                        # Données brutes
│   ├── processed/                  # Données traitées
│   └── models/                     # Modèles sauvegardés
│
├── sql/
│   ├── create_tables.sql           # Scripts création tables
│   ├── views.sql                   # Vues pour Power BI
│   └── procedures.sql              # Procédures stockées
│
├── logs/                           # Fichiers de logs
│
├── tests/
│   ├── test_extraction.py
│   ├── test_transformation.py
│   └── test_models.py
│
├── main.py                         # Script principal ETL
├── requirements.txt                # Dépendances Python
├── .env                           # Variables d'environnement
└── README.md                      # Documentation


InstagramETL/
├─ config/
│  └─ settings.py
├─ data/
│  ├─ raw/               # JSON bruts extraits depuis l'API
│  └─ processed/         # CSV / fichiers transformés
├─ etl/
│  ├─ extract.py
│  ├─ transform.py
│  ├─ load.py
│  └─ pipeline.py
├─ scripts_models/
│  ├─ train_and_select.py
│  └─ predict.py
─ models/
├─ sql/
│  └─ schema.sql
    --views.sql 
├─ requirements.txt
├─ .env.example
└─ README.md


creer une table rm dans le schemla stage . charger les donnee qui serons envoyer au format csv .
planifier l'envoie automatique par mails du rapport qui sera aussi partager sous un format excel
destinataire. nous trois + Mr charle