# Controle Qualite

**Statut:** En cours de developpement
**Derniere mise a jour:** 2026-02-17
**Fonctionnalite:** Badge qualite, scoring automatique, surveillance de derive

---

## Vue d'Ensemble

Le module de controle qualite de VarunaPoC evalue automatiquement la qualite des lames numerisees et surveille les performances des modeles d'intelligence artificielle dans le temps. Il aide les pathologistes a identifier rapidement les lames de mauvaise qualite et les administrateurs a detecter les problemes de derive des modeles.

---

## Badge Qualite

### Principe

Chaque lame recoit un **badge qualite** automatique apres analyse. Ce badge est visible dans l'explorateur de lames et dans la visionneuse.

### Niveaux de Qualite

| Badge | Couleur | Score | Signification |
|-------|---------|-------|---------------|
| **Excellente** | Vert | 0.8 -- 1.0 | Lame de haute qualite, exploitable sans reserve |
| **Bonne** | Vert clair | 0.6 -- 0.8 | Qualite acceptable pour le diagnostic |
| **Moyenne** | Jaune | 0.4 -- 0.6 | Qualite reduite, verifier les zones problematiques |
| **Insuffisante** | Orange | 0.2 -- 0.4 | Artefacts importants, re-numerisation recommandee |
| **Inexploitable** | Rouge | 0.0 -- 0.2 | Lame inutilisable, re-numerisation necessaire |

### Ou le Voir

- **Dans l'explorateur :** Le badge apparait a cote du nom de la lame
- **Dans la visionneuse :** Le badge est affiche dans le panneau d'informations
- **Dans le panneau ML :** Le score detaille est disponible

---

## Scoring Automatique

### Comment ca Fonctionne

Le scoring automatique analyse la lame pour detecter les artefacts courants qui peuvent affecter le diagnostic :

| Artefact | Description | Impact |
|----------|-------------|--------|
| **Flou** | Zones hors focus | Diagnostic difficile dans les zones floues |
| **Pli** | Tissu replie sur lui-meme | Superposition de structures, fausse interpretation |
| **Bulle** | Bulle d'air sous la lamelle | Zone non observable |
| **Tache** | Tache ou debris sur la lame | Masque le tissu sous-jacent |
| **Bord** | Zone en bordure de lame mal numerisee | Tissu incomplet |

### Resultat du Scoring

Pour chaque lame, le systeme fournit :

1. **Score global** : Note de 0 a 1 (1 = qualite parfaite)
2. **Label qualite** : Texte descriptif (Excellente, Bonne, etc.)
3. **Liste d'artefacts** : Chaque artefact detecte avec :
   - Type (flou, pli, bulle, etc.)
   - Severite (faible, moderee, elevee)
   - Localisation (coordonnees sur la lame)
   - Surface affectee (pourcentage de la lame)
4. **Recommandation** : Action suggeree (ex : "Lame exploitable" ou "Re-numerisation recommandee")

### Lancer une Evaluation

1. Ouvrez une lame dans la visionneuse
2. Dans le panneau ML, cliquez sur **"Evaluer la qualite"**
3. Le resultat s'affiche en quelques secondes

---

## Surveillance de Derive (Drift Monitoring)

### Qu'est-ce que la Derive ?

La derive (ou "drift") designe une degradation progressive des performances d'un modele d'IA dans le temps. Cela peut survenir lorsque :

- Les lames analysees different de celles utilisees pour l'entrainement
- Le protocole de coloration change
- Le scanner est recalibre ou remplace
- La population de patients evolue

### Comment VarunaPoC Detecte la Derive

Le systeme surveille en continu plusieurs metriques :

| Metrique | Description | Seuil d'Alerte |
|----------|-------------|----------------|
| **Taux de rejet** | Pourcentage de detections rejetees par les pathologistes | > 30% |
| **Score de confiance moyen** | Confiance moyenne des predictions | < 0.6 |
| **Distribution des predictions** | Repartition des classes predites | Ecart significatif |
| **Variance des embeddings** | Dispersion des representations numeriques | Ecart significatif |

### Rapport de Derive

Le rapport de derive est accessible aux administrateurs techniques et contient :

- **Modele concerne** : Identifiant et version du modele
- **Date du rapport** : Periode analysee
- **Metriques** : Valeur actuelle, seuil, statut (normal ou en derive)
- **Diagnostic global** : Le modele est-il en derive ? (oui/non)
- **Recommandation** : Action suggeree

### Exemple de Rapport

```
Modele : gleason_grading_v2
Periode : 7 derniers jours
Statut : DERIVE DETECTEE

Metriques :
  - Taux de rejet    : 35% (seuil: 30%) -> EN DERIVE
  - Confiance moyenne : 0.58 (seuil: 0.60) -> EN DERIVE
  - Distribution      : Normal

Recommandation : Re-entrainement recommande avec les corrections
des 30 derniers jours.
```

### Que Faire en Cas de Derive ?

1. **Verifier les corrections recentes** : Y a-t-il un changement de protocole ?
2. **Examiner les lames recentes** : Sont-elles differentes des lames d'entrainement ?
3. **Consulter l'administrateur technique** : Un re-entrainement peut etre necessaire
4. **Augmenter temporairement le seuil de confiance** pour reduire les faux positifs

---

## Bonnes Pratiques

### Pour les Pathologistes

- Verifiez le **badge qualite** avant d'analyser une lame
- Si le badge est orange ou rouge, examinez la lame avec precaution
- Fournissez un **retour systematique** sur les detections pour alimenter la surveillance
- Signalez les changements de protocole de coloration ou de scanner

### Pour les Administrateurs

- Consultez les **rapports de derive** chaque semaine
- Planifiez un **re-entrainement** des modeles lorsque la derive est detectee
- Surveillez le **taux de rejet** global : un pic soudain indique un probleme
- Documentez les changements de materiel ou de protocole

---

## Depannage

### Le badge qualite ne s'affiche pas

**Causes possibles :**
- Le service de qualite n'est pas active sur le serveur
- La lame n'a pas encore ete evaluee

**Solution :**
1. Lancez manuellement l'evaluation depuis le panneau ML
2. Contactez l'administrateur pour verifier la configuration

### Le rapport de derive indique une derive permanente

**Causes possibles :**
- Le modele n'a jamais ete re-entraine avec les nouvelles donnees
- Le type de lames analyse a fondamentalement change

**Solution :**
1. Verifiez si les corrections des pathologistes sont bien prises en compte
2. Planifiez un re-entrainement du modele
3. Contactez l'equipe technique pour une analyse approfondie

---

## Prochaines Etapes

- **[07-ML_FEATURES.md](./07-ML_FEATURES.md)** : Revenez aux fonctionnalites d'IA
- **[06-ANNOTATIONS.md](./06-ANNOTATIONS.md)** : Apprenez a annoter et corriger
- **[99-FAQ.md](./99-FAQ.md)** : Questions frequentes

---

**Version:** 1.0
**Derniere revision:** 2026-02-17
**Auteur:** Equipe VarunaPoC
