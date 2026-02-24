# fhir

## But
Module FHIR R4 pour la generation de ressources cliniques (DiagnosticReport, Patient, Observation) et le lancement SMART on FHIR.

## Pourquoi
L'interoperabilite avec les systemes hospitaliers (EHR) necessite la production de ressources conformes aux standards FHIR R4, US Core, CA Core et mCODE.

## Structure
- `__init__.py` -- Point d'entree ; expose le flag `FHIR_ENABLED`.
- `capability.py` -- Construction du CapabilityStatement FHIR R4 decrivant les capacites du serveur.
- `resources.py` -- Builders de ressources DiagnosticReport avec Specimen, Observation et Patient contenus.
- `profiles.py` -- Builders de profils US Core Patient, CA Core Patient, mCODE CancerCondition/TNM/TumorMarker.
- `patient_context.py` -- Extraction du contexte patient depuis les parametres URL ou le lancement SMART.
- `smart.py` -- Gestionnaire de lancement SMART on FHIR et configuration .well-known/smart-configuration.
- `routes.py` -- Endpoints FastAPI pour metadata, DiagnosticReport, Patient, Condition, Observation, launch.
