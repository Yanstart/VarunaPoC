# runner

## But
Stack Docker pour le runner GitHub Actions self-hosted, executant les pipelines CI/CD du projet localement.

## Pourquoi
Un runner self-hosted permet d'executer les workflows GitHub Actions sur la VM de developpement avec acces direct au code, aux slides et a Docker, sans dependre des minutes GitHub gratuites.

## Structure
- `docker-compose.yml` : 4 replicas du runner (myoung34/github-runner) + 1 registry Docker locale (port 5000)
- `.env.example` : template de configuration (REPO_URL, ACCESS_TOKEN, RUNNER_REPLICAS)
- `.env` : configuration active (ne pas commiter)
- `act-secrets.example` : template de secrets pour tests locaux avec `act`
- `cleanup.sh` : script de nettoyage hebdomadaire Docker (images, cache buildx, volumes, reseaux >7 jours)
- `act-events/` : evenements JSON simulant push et pull_request pour tests locaux
