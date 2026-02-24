# .dvc

## But
Configuration DVC (Data Version Control) pour le versioning des datasets ML et lames histologiques.

## Pourquoi
Les fichiers de donnees medicales (lames, modeles ML) sont trop volumineux pour Git. DVC permet de les versionner via un stockage distant S3-compatible (MinIO).

## Structure
- `config.example` : exemple de configuration DVC avec remotes MinIO (primaire), backup et cloud (AWS/Azure/GCP), parametres de cache et commandes utiles
