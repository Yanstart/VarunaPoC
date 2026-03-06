# Keycloak : Fix realm-export.json authenticationFlows

## Probleme

Keycloak 23.0 crashait au demarrage avec :

```
ERROR: Cannot invoke "org.keycloak.models.AuthenticationFlowModel.getId()"
because "flow" is null
```

## Cause

Dans `backend/keycloak/realm-export.json` :

```json
{
  "authenticationFlows": [],          // Vide !
  "browserFlow": "browser",           // Reference un flow qui n'existe pas
  "registrationFlow": "registration", // Idem
  "directGrantFlow": "direct grant",  // Idem
  ...
}
```

Les champs `browserFlow`, `registrationFlow`, etc. referencent des flows
par nom, mais `authenticationFlows` est un tableau vide. Keycloak ne peut
pas resoudre ces references et crash avec un NPE.

## Solution

Supprimer les references aux flows vides. Keycloak utilise ses flows internes
par defaut quand rien n'est specifie.

Lignes supprimees du `realm-export.json` :
```json
"authenticationFlows": [],
"authenticatorConfig": [],
"requiredActions": [],
"browserFlow": "browser",
"registrationFlow": "registration",
"directGrantFlow": "direct grant",
"resetCredentialsFlow": "reset credentials",
"clientAuthenticationFlow": "clients",
"dockerAuthenticationFlow": "docker auth",
```

## Insight

Un realm-export.json genere manuellement (pas exporte depuis un Keycloak existant)
risque d'avoir des references pendantes. Les flows d'authentification sont complexes
(browser, registration, direct grant, etc.) et il est preferable de les laisser
se creer automatiquement par Keycloak plutot que de les definir a vide.

## Fichier modifie

- `backend/keycloak/realm-export.json`
