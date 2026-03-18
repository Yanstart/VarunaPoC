# Interview Pathologiste : Workflow d'Annotation et Correction IA

**Date:** 2026-03-18
**Interviewe:** Dr. Varun Patil (persona pathologiste senior, CHU UCL Namur)
**Interviewer:** Frontend Tech Lead

## Points Cles Extraits

### Annotation - 4 gestes, par frequence
1. **Cercle rapide / dessin libre** (60%) — delimiter une zone d'interet, geste grossier
2. **Fleche + texte** (25%) — pointer un detail precis avec 2-3 mots
3. **Contour precis / polygone** (10%) — mesure de surface, publication
4. **Rectangle de selection** (5%) — capture d'ecran / export

### Correction IA - 3 actions, 1-2 clics max
- **V** = Valider (zone passe en vert, confirme)
- **X** = Rejeter (zone disparait, faux positif)
- **Drag bords** = Corriger le contour (redimensionner, pas redessiner)
- **Tab** = Passer a la detection suivante (tri par confiance decroissante)

### Raccourcis clavier essentiels
| Touche | Action |
|--------|--------|
| Molette | Zoom |
| Espace+drag | Pan |
| D | Dessin libre |
| F | Fleche |
| R | Rectangle |
| Echap | Annuler outil |
| Ctrl+Z | Undo (non negociable) |
| Suppr | Supprimer annotation |
| V | Valider detection IA |
| X | Rejeter detection IA |
| Tab | Detection suivante |
| H | Masquer/afficher annotations |
| 1-5 | Zoom predefini (2x/5x/10x/20x/40x) |
| L | Ouvrir labels |

### Principes de design
1. **1 touche = 1 action** (pas de Ctrl+Shift+Alt)
2. **Raccourcis actifs globalement** (pas besoin de cliquer dans un panneau d'abord)
3. **Dessin libre fluide** comme un stylo, fermeture automatique
4. **Toggle IA on/off** (H) pour voir la lame "propre"
5. **Tri par confiance** decroissante, seuil configurable
6. **Labels pathologiques** sur les detections (pas juste un %)
7. **Feedback visible** : montrer l'impact des corrections sur la precision du modele

### Conditions pour contribuer a l'entrainement IA
1. Ne pas ralentir (5 min max de plus par lame)
2. Voir le resultat (dashboard precision du modele)
3. Donnees patients restent dans l'hopital

### Formation residents
- Annotations comme "jalons de randonnnee" sur la lame
- Mode quiz : annotation visible, texte masque
- Suivi de progression (% identification correcte par type de lesion)

## Interview Complete

[Voir le transcript complet dans le chat du 2026-03-18]
