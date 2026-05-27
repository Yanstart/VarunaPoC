---
name: varuna-tfe-sourcing-academique
description: Protocole pour sourcer toute affirmation forte du TFE. Hiérarchie de qualité des sources, format BibLaTeX, vérification DOI/ISBN, anti-patterns à refuser.
allowed-tools: Read, Write, Edit, WebFetch, WebSearch
---

# Sourcing académique — protocole

## Quand une affirmation doit-elle être sourcée ?

Toute phrase qui :
- Énonce un fait scientifique ou statistique
- Cite une méthode établie (saturation théorique, UTAUT, etc.)
- Mentionne un cadre réglementaire (RGPD, AI Act, ISO)
- Affirme un état de l'art ou de marché ("la majorité des laboratoires…")
- Reprend une définition technique

Et **toute** affirmation contestable hors verbatim d'entretien.

**Pas besoin de sourcer** : ce qui relève des observations propres du TFE (analyse des entretiens, présentation de Varuna comme objet construit par les auteurs).

## Hiérarchie de qualité (du plus fort au plus faible)

| Rang | Type | Exemple |
|---|---|---|
| 1 | Article peer-reviewed indexé | Nature Medicine, JAMA, Lancet Oncology |
| 2 | Texte officiel UE / national | Règlement, directive, ISO, KCE, HAS, CNIL |
| 3 | Préprint reconnu (arXiv, bioRxiv, medRxiv) | À utiliser SI pas d'équivalent peer-reviewed |
| 4 | Document institutionnel | Rapport HAS, INAMI, EMA, FDA, OMS |
| 5 | Ouvrage de référence avec ISBN | Manuel universitaire reconnu |
| 6 | Rapport technique d'organisme reconnu | KCE Belgique, CHU UCL Namur (doc interne 2022) |
| 7 | Site web institutionnel daté | EUR-Lex, OECD.AI |

**Bannis pour citation** :
- Blogs personnels ou commerciaux
- Sites de vendeurs (sauf documentation technique factuelle, marquée comme telle)
- Articles de presse généraliste (peuvent illustrer un point mais ne SOURCENT pas)
- Wikipedia (acceptable pour explorer, jamais pour citer)
- Posts LinkedIn / X / forums (sauf comme matériau d'analyse, cf. agent personas)

## Procédure de sourcing (5 étapes)

### Étape 1 — Identifier le claim à sourcer

Lire le chapitre cible et repérer :
- Les `% [TODO sources]` laissés par le rédacteur
- Les affirmations fortes sans `\cite{}`
- Les statistiques sans référence

### Étape 2 — Recherche dans la biblio existante

`Grep` sur `Report/refs/varuna.bib` :
- Peut-être un papier déjà présent couvre le claim
- Privilégier la réutilisation aux nouveaux ajouts (limite l'inflation biblio)

### Étape 3 — Recherche externe (si nécessaire)

Sources recommandées :
- **PubMed** : <https://pubmed.ncbi.nlm.nih.gov/> (médical, peer-reviewed)
- **Google Scholar** : <https://scholar.google.com> (généraliste, à filtrer)
- **EUR-Lex** : <https://eur-lex.europa.eu> (textes officiels UE)
- **HAS** : <https://www.has-sante.fr> (recommandations FR)
- **KCE Belgique** : <https://kce.fgov.be> (rapports techniques santé Belgique)
- **INAMI** : <https://www.inami.fgov.be> (cadre belge)
- **arXiv** : <https://arxiv.org/list/cs.CV/recent> (IA en vision)

Utiliser `WebSearch` pour explorer, puis `WebFetch` pour valider la source.

### Étape 4 — Vérification obligatoire

Avant ajout à `varuna.bib` :
- [ ] Auteur(s) identifiable(s)
- [ ] DOI (article) ou ISBN (livre) ou URL officielle (texte légal) **vérifiable**
- [ ] Date de publication cohérente
- [ ] Pour les sites web : date d'accès notée
- [ ] Source lue (pas juste vue dans la liste de résultats)

### Étape 5 — Ajout au .bib et au texte

Format BibLaTeX standard :
```bibtex
@article{auteurAnneeMotcle,
  author    = {Nom, Prénom and AutreNom, AutrePrénom},
  title     = {Titre exact},
  journal   = {Nom du journal},
  volume    = {N},
  number    = {N},
  pages     = {DD--DDD},
  year      = {YYYY},
  doi       = {10.XXXX/...}
}
```

Convention de clés : `<premier-auteur-lowercase><année>[motcle]`
Exemples : `mahmood2024uni`, `bejnordi2017lymph`, `rgpd2016`, `aiact2024`

Citation dans le texte LaTeX :
```latex
Le domain shift constitue un obstacle majeur à l'adoption clinique de l'IA \cite{stacke2020}.
```

## Cas particuliers

### Texte légal UE

```bibtex
@misc{aiact2024,
  title        = {Règlement (UE) 2024/1689 du Parlement européen et du Conseil
                  du 13 juin 2024 établissant des règles harmonisées concernant
                  l'intelligence artificielle (Règlement sur l'intelligence artificielle)},
  organization = {Journal officiel de l'Union européenne},
  year         = {2024},
  url          = {https://eur-lex.europa.eu/eli/reg/2024/1689},
  urldate      = {2026-05-24},
  note         = {L 1689}
}
```

### Document interne (rapport CHU)

```bibtex
@techreport{denizza2022,
  author      = {De Nizza, Damien},
  title       = {Digital Pathology — Digitalisation et Télé-expertise,
                 Laboratoire d'anatomopathologie},
  institution = {CHU UCL Namur},
  type        = {Présentation interne},
  year        = {2022},
  month       = dec,
  day         = {12}
}
```

### Article avec auteurs nombreux

Utiliser `and others` après les 3 premiers auteurs (BibLaTeX le rend en "et al." automatiquement avec `maxnames=3` au preamble).

## Anti-patterns à refuser

- **Citation fantôme** : ajouter `\cite{XXX}` sans avoir lu XXX
- **Citation in-extenso** : citer 10 sources pour une seule affirmation banale
- **Citation décorative** : `\cite{...}` derrière une affirmation déjà évidente
- **Citation périmée** : 2008 pour un état de l'art actuel sur l'IA
- **Citation circulaire** : citer un blog qui cite la même source primaire

## Output

Mise à jour de `Report/refs/varuna.bib` + remplacement des `% [TODO sources]` par les `\cite{key}` correspondants dans les chapitres concernés.
