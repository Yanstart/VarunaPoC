# Sources Officielles - VarunaPoC

**But:** Reference centralisee des sources autorisees pour valider les propositions.

**Regle:** Toute proposition technique DOIT etre verifiable par une source listee ici.

---

## Librairies Core du Projet

### OpenSlide (Backend - Lecture WSI)
- **Site:** https://openslide.org/
- **API Python:** https://openslide.org/api/python/
- **Formats supportes:** https://openslide.org/formats/
- **GitHub Issues:** https://github.com/openslide/openslide/issues
- **Usage:** Lecture de tous les formats de lames histologiques (10 formats, 94 lames testees)

### OpenSeadragon (Frontend - Viewer Gigapixel)
- **Site:** https://openseadragon.github.io/
- **Documentation:** https://openseadragon.github.io/docs/
- **Exemples:** https://openseadragon.github.io/examples/
- **Coordonnees viewport:** https://openseadragon.github.io/examples/viewport-coordinates/
- **GitHub:** https://github.com/openseadragon/openseadragon
- **Usage:** Affichage et navigation dans les images gigapixel

### FastAPI (Backend - Framework Web)
- **Site:** https://fastapi.tiangolo.com/
- **Tutorial:** https://fastapi.tiangolo.com/tutorial/
- **Reference API:** https://fastapi.tiangolo.com/reference/
- **Security:** https://fastapi.tiangolo.com/tutorial/security/
- **Usage:** API REST pour servir les tuiles, annotations et inference ML

### Vite (Frontend - Build Tool)
- **Site:** https://vitejs.dev/
- **Guide:** https://vitejs.dev/guide/
- **Config:** https://vitejs.dev/config/
- **Usage:** Serveur de developpement et build de production

---

## Phase 2 - Annotations & Base de Donnees

### PostgreSQL + PostGIS (Base de donnees annotations)
- **PostgreSQL:** https://www.postgresql.org/docs/15/
- **PostGIS:** https://postgis.net/documentation/
- **PostGIS Geometry:** https://postgis.net/docs/geometry.html
- **Usage:** Stockage annotations avec geometries spatiales (SRID=0, coordonnees pixels)

### SQLAlchemy (ORM async)
- **Site:** https://www.sqlalchemy.org/
- **Async:** https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- **Usage:** ORM pour models Annotation/AnnotationLabel, async engine

### GeoAlchemy2 (PostGIS pour SQLAlchemy)
- **Documentation:** https://geoalchemy-2.readthedocs.io/
- **Usage:** Types Geometry dans SQLAlchemy, index spatiaux automatiques

### Alembic (Migrations DB)
- **Documentation:** https://alembic.sqlalchemy.org/
- **Tutorial:** https://alembic.sqlalchemy.org/en/latest/tutorial.html
- **Usage:** Migrations schema DB (versions/001_create_annotations.py)
- **Note:** Necessite `load_dotenv()` explicite dans env.py

### Shapely (Geometries Python)
- **Documentation:** https://shapely.readthedocs.io/
- **Usage:** Simplification de contours, conversion vers GeoJSON dans pipeline detection

---

## Phase 2 - ML & Detection

### Slideflow (ML pour WSI)
- **Site:** https://slideflow.dev/
- **Documentation:** https://slideflow.dev/docs/
- **GitHub:** https://github.com/jamesdolezal/slideflow
- **Usage:** Framework ML pour lames histologiques. Integration Phikon-v2, heatmaps, predictions
- **Limitation:** Ne supporte pas DICOM ni Generic TIFF sans MPP metadata

### Phikon-v2 (Foundation Model Pathologie)
- **HuggingFace:** https://huggingface.co/owkin/phikon-v2
- **Paper:** DINO-based pathology foundation model (Owkin)
- **Usage:** Feature extraction pour heatmaps d'attention (64x64, ~2.5min GPU CUDA)
- **Prerequis:** transformers>=4.22 pour `AutoImageProcessor`

### SciPy (Traitement scientifique)
- **Documentation:** https://docs.scipy.org/doc/scipy/
- **ndimage:** https://docs.scipy.org/doc/scipy/reference/ndimage.html
- **Usage:** `scipy.ndimage.label()` pour segmentation regions dans heatmaps

### scikit-image (Traitement d'images)
- **Documentation:** https://scikit-image.org/docs/stable/
- **Contours:** https://scikit-image.org/docs/stable/api/skimage.measure.html
- **Usage:** `skimage.measure.find_contours()` pour extraction contours regions

### Pillow (Image Processing)
- **Documentation:** https://pillow.readthedocs.io/
- **Usage:** Manipulation d'images Python, generation thumbnails/overviews

### Pydantic
- **Documentation:** https://docs.pydantic.dev/
- **Usage:** Validation de donnees et schemas (AnnotationCreate, DetectionResult, GeoJSON)

---

## Standards Medicaux

### DICOM (Digital Imaging and Communications in Medicine)
- **Site officiel:** https://www.dicomstandard.org/
- **PS3.3 (IODs):** https://dicom.nema.org/medical/dicom/current/output/html/part03.html
- **Supplement 145 (WSI):** Whole Slide Microscopic Image IOD
- **Usage:** Standard pour l'imagerie medicale et integration PACS

### IVDR (In Vitro Diagnostic Regulation)
- **Texte:** https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32017R0746
- **Usage:** Classification reglementaire (Classe A pour recherche, Classe C pour diagnostic)

### HL7 (Health Level 7)
- **Site:** https://www.hl7.org/
- **FHIR:** https://hl7.org/fhir/
- **Usage:** Interoperabilite avec systemes hospitaliers (Phase 3+)

---

## Securite & Conformite

### OWASP (Open Web Application Security Project)
- **Top 10:** https://owasp.org/www-project-top-ten/
- **ASVS:** https://owasp.org/www-project-application-security-verification-standard/
- **Cheat Sheets:** https://cheatsheetseries.owasp.org/
- **Usage:** Reference pour securite applicative

### HIPAA (USA) / RGPD (EU)
- **HIPAA Security Rule:** https://www.hhs.gov/hipaa/for-professionals/security/
- **RGPD:** https://www.cnil.fr/fr/rgpd-de-quoi-parle-t-on
- **MDR (Medical Device Regulation):** https://health.ec.europa.eu/medical-devices-sector/new-regulations_en
- **Usage:** Conformite pour donnees de sante

### NIST (National Institute of Standards and Technology)
- **Cybersecurity Framework:** https://www.nist.gov/cyberframework
- **800-53 (Controls):** https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final
- **Usage:** Standards de securite gouvernementaux

---

## MLOps & Machine Learning (Post-MVP)

### MLflow
- **Site:** https://mlflow.org/
- **Documentation:** https://mlflow.org/docs/latest/index.html
- **Tracking:** https://mlflow.org/docs/latest/tracking.html
- **Model Registry:** https://mlflow.org/docs/latest/model-registry.html
- **Usage:** Tracking des experiences, registre des modeles (Phase 3+)

### DVC (Data Version Control)
- **Site:** https://dvc.org/
- **Documentation:** https://dvc.org/doc
- **Usage:** Versioning des datasets et pipelines ML (Phase 3+)

### PyTorch
- **Site:** https://pytorch.org/
- **Documentation:** https://pytorch.org/docs/stable/index.html
- **Tutorials:** https://pytorch.org/tutorials/
- **Usage:** Framework pour modeles deep learning (utilise via Slideflow)

### Evidently AI (Drift Detection)
- **Site:** https://www.evidentlyai.com/
- **Documentation:** https://docs.evidentlyai.com/
- **Usage:** Detection de drift dans les predictions ML (Phase 3+)

### CLAM (Computational Pathology)
- **GitHub:** https://github.com/mahmoodlab/CLAM
- **Paper:** https://www.nature.com/articles/s41551-020-00682-w
- **Usage:** Reference pour analyse WSI avec attention-based MIL

---

## Infrastructure & DevOps

### Docker
- **Documentation:** https://docs.docker.com/
- **Compose:** https://docs.docker.com/compose/
- **Usage:** Containerisation des services

### Kubernetes
- **Documentation:** https://kubernetes.io/docs/
- **Concepts:** https://kubernetes.io/docs/concepts/
- **Usage:** Orchestration de containers en production (Phase 3+)

### Prometheus (Monitoring)
- **Documentation:** https://prometheus.io/docs/
- **Query Language:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Usage:** Collection de metriques (monitoring.py optionnel)

### Grafana (Dashboards)
- **Documentation:** https://grafana.com/docs/
- **Usage:** Visualisation des metriques Prometheus

### Nginx
- **Documentation:** https://nginx.org/en/docs/
- **Usage:** Reverse proxy, load balancing, cache

### GitHub Actions (CI/CD)
- **Documentation:** https://docs.github.com/en/actions
- **Usage:** CI/CD (lint, tests, Docker build, Trivy, Bandit, CodeQL, Gitleaks)

---

## JavaScript & Web

### MDN Web Docs
- **Site:** https://developer.mozilla.org/
- **JavaScript:** https://developer.mozilla.org/en-US/docs/Web/JavaScript
- **Canvas API:** https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API
- **SVG:** https://developer.mozilla.org/en-US/docs/Web/SVG
- **Usage:** Reference pour JavaScript, APIs Web, SVG (annotations overlay)

### Chrome DevTools
- **Documentation:** https://developer.chrome.com/docs/devtools/
- **Performance:** https://developer.chrome.com/docs/devtools/performance/
- **Usage:** Debug et profiling frontend

---

## Python

### Python Official
- **Documentation:** https://docs.python.org/3/
- **PEP 8 (Style):** https://peps.python.org/pep-0008/
- **Usage:** Reference langage Python

---

## Phase 3.1 - Authentification

### Keycloak (Identity Provider)
- **Site:** https://www.keycloak.org/
- **Documentation:** https://www.keycloak.org/documentation
- **Admin REST API:** https://www.keycloak.org/docs-api/latest/rest-api/
- **Usage:** IdP OIDC pour developpement et tests. 4 test users (dr.martin, nurse.dupont, admin, viewer), port 8180

### OIDC (OpenID Connect)
- **Specification:** https://openid.net/specs/openid-connect-core-1_0.html
- **PKCE:** https://datatracker.ietf.org/doc/html/rfc7636
- **Usage:** Protocol d'authentification standard pour le flow PKCE frontend

### PyJWT
- **Documentation:** https://pyjwt.readthedocs.io/
- **Usage:** Validation JWT RS256/ES256 avec JWKS

---

## Outils PACS (Phase 3)

### Orthanc
- **Site:** https://www.orthanc-server.com/
- **Book:** https://book.orthanc-server.com/
- **Usage:** Serveur PACS open source

### pynetdicom
- **Documentation:** https://pydicom.github.io/pynetdicom/
- **Usage:** Implementation DICOM networking en Python (C-FIND, C-MOVE, C-GET, C-STORE)

---

## Utilisation de ce Document

### Pour Valider une Proposition

1. Identifier le domaine (backend, frontend, securite, etc.)
2. Trouver la source officielle correspondante
3. Verifier que la proposition est conforme a la documentation
4. Citer la source dans la justification

### Pour Ajouter une Source

```markdown
### [Nom de l'Outil/Standard]
- **Site:** [URL principale]
- **Documentation:** [URL docs]
- **Usage:** [A quoi ca sert dans le projet]
```

### Verification Croisee

Toute proposition importante devrait etre verifiable par:
1. **Source primaire:** Documentation officielle de l'outil
2. **Source secondaire:** GitHub issues ou discussions de la communaute
3. **Test pratique:** Verification dans notre codebase

---

**Derniere mise a jour:** 2026-02-12
