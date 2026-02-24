# act-events

## But
Fichiers JSON simulant des evenements GitHub pour tester les workflows localement avec `act`.

## Pourquoi
Permettre de debugger les workflows CI/CD sans pousser de code sur GitHub, en simulant des evenements push et pull_request avec des payloads realistes.

## Structure
- `push.json` : evenement push vers main (ref, commit, repository)
- `pull_request.json` : evenement pull_request opened (numero, branches head/base)
