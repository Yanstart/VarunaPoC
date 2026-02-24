# .github

## But
CI/CD GitHub Actions et runner self-hosted.

## Pourquoi
Automatiser build, tests, securite, et deploiement. Le runner self-hosted tourne sur la VM pour eviter les couts GitHub Actions cloud.

## Structure
```
.github/
  workflows/             # Pipelines CI/CD (build, test, security scan, deploy)
  runner/                # Docker Compose pour 4 runners self-hosted + 1 registry
    docker-compose.yml   # 4 replicas runner + registry container
```

## Notes
- Demarrage: `cd .github/runner && docker compose up -d`
- ATTENTION: `docker system prune -a` tue les runners -> redemarrer apres
