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
- **Usage:** Lecture de tous les formats de lames histologiques

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
- **Usage:** API REST pour servir les tuiles et metadonnees

### Vite (Frontend - Build Tool)
- **Site:** https://vitejs.dev/
- **Guide:** https://vitejs.dev/guide/
- **Config:** https://vitejs.dev/config/
- **Usage:** Serveur de developpement et build de production

---

## Standards Medicaux

### DICOM (Digital Imaging and Communications in Medicine)
- **Site officiel:** https://www.dicomstandard.org/
- **PS3.3 (IODs):** https://dicom.nema.org/medical/dicom/current/output/html/part03.html
- **Supplement 145 (WSI):** Whole Slide Microscopic Image IOD
- **Usage:** Standard pour l'imagerie medicale et integration PACS

### HL7 (Health Level 7)
- **Site:** https://www.hl7.org/
- **FHIR:** https://hl7.org/fhir/
- **Usage:** Interoperabilite avec systemes hospitaliers

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

## MLOps & Machine Learning

### MLflow
- **Site:** https://mlflow.org/
- **Documentation:** https://mlflow.org/docs/latest/index.html
- **Tracking:** https://mlflow.org/docs/latest/tracking.html
- **Model Registry:** https://mlflow.org/docs/latest/model-registry.html
- **Usage:** Tracking des experiences, registre des modeles

### DVC (Data Version Control)
- **Site:** https://dvc.org/
- **Documentation:** https://dvc.org/doc
- **Usage:** Versioning des datasets et pipelines ML

### PyTorch
- **Site:** https://pytorch.org/
- **Documentation:** https://pytorch.org/docs/stable/index.html
- **Tutorials:** https://pytorch.org/tutorials/
- **Usage:** Framework pour modeles deep learning

### TensorFlow
- **Site:** https://www.tensorflow.org/
- **Documentation:** https://www.tensorflow.org/api_docs
- **Usage:** Alternative a PyTorch pour deep learning

### Evidently AI (Drift Detection)
- **Site:** https://www.evidentlyai.com/
- **Documentation:** https://docs.evidentlyai.com/
- **Usage:** Detection de drift dans les predictions ML

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
- **Usage:** Orchestration de containers en production

### Prometheus (Monitoring)
- **Documentation:** https://prometheus.io/docs/
- **Query Language:** https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Usage:** Collection de metriques

### Grafana (Dashboards)
- **Documentation:** https://grafana.com/docs/
- **Usage:** Visualisation des metriques Prometheus

### Nginx
- **Documentation:** https://nginx.org/en/docs/
- **Usage:** Reverse proxy, load balancing, cache

---

## JavaScript & Web

### MDN Web Docs
- **Site:** https://developer.mozilla.org/
- **JavaScript:** https://developer.mozilla.org/en-US/docs/Web/JavaScript
- **Canvas API:** https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API
- **Usage:** Reference pour JavaScript et APIs Web

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

### Pillow (Image Processing)
- **Documentation:** https://pillow.readthedocs.io/
- **Usage:** Manipulation d'images Python

### Pydantic
- **Documentation:** https://docs.pydantic.dev/
- **Usage:** Validation de donnees et settings

---

## Outils PACS

### Orthanc
- **Site:** https://www.orthanc-server.com/
- **Book:** https://book.orthanc-server.com/
- **Usage:** Serveur PACS open source

### pynetdicom
- **Documentation:** https://pydicom.github.io/pynetdicom/
- **Usage:** Implementation DICOM networking en Python

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

**Derniere mise a jour:** 2026-01-29
