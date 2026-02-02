"""
Tag Router Service
Routage intelligent vers modèles ML spécialisés basé sur tags.

Références:
- docs/MLOPS_ARCHITECTURE.md Section 2.3
- Tag-based ML routing pattern (Uber Michelangelo, Netflix)
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelRoute:
    """
    Route vers modèle ML spécialisé.

    Attributes:
        model_id: Identifiant unique modèle
        model_name: Nom lisible
        model_version: Version (semantic versioning)
        model_path: Chemin vers artefact MLflow
        priority: Priorité si plusieurs matchs (100 = haute, 1 = fallback)
        min_confidence: Seuil confiance minimum pour prédiction
        task_type: Type de tâche (classification, segmentation, etc.)
        required_tags: Tags requis pour ce modèle
        description: Description clinique
        reference_metrics: Metrics de référence (performance)
    """
    model_id: str
    model_name: str
    model_version: str
    model_path: str
    priority: int
    min_confidence: float
    task_type: str
    required_tags: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    clinical_use: str = ""
    reference_metrics: Dict[str, float] = field(default_factory=dict)


class TagRouter:
    """
    Routeur intelligent basé sur tags.

    Workflow:
    1. Reçoit tags d'une slide (organ, stain, marker, task)
    2. Recherche modèle(s) correspondant(s) dans configuration
    3. Sélectionne meilleur match par priorité
    4. Retourne route vers modèle MLflow

    Références:
    - Tag-based routing pattern (Uber Michelangelo)
    - Multi-model serving architecture (Netflix)

    Usage:
        router = TagRouter("config/ml_routes.yaml")
        tags = {"organ": "prostate", "stain": "H&E", "task": "grading"}
        route = router.route(tags)
        # route.model_path = "models:/gleason_grading/production"
    """

    def __init__(self, routes_config_path: str = "config/ml_routes.yaml"):
        """
        Initialize router avec configuration.

        Args:
            routes_config_path: Chemin vers ml_routes.yaml
        """
        self.config_path = routes_config_path
        self.routes: List[ModelRoute] = []
        self.fallback_model: Optional[ModelRoute] = None
        self.routing_config: Dict = {}

        self._load_configuration()

    def _load_configuration(self):
        """
        Charge configuration depuis YAML.

        Raises:
            FileNotFoundError: Si config file inexistant
            ValueError: Si configuration invalide
        """
        config_file = Path(self.config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Parse routes
            routes_data = config.get('routes', [])
            for route_data in routes_data:
                route = ModelRoute(
                    model_id=route_data['model_id'],
                    model_name=route_data['model_name'],
                    model_version=route_data['model_version'],
                    model_path=route_data['model_path'],
                    priority=route_data['priority'],
                    min_confidence=route_data['min_confidence'],
                    task_type=route_data['task_type'],
                    required_tags=route_data.get('required_tags', {}),
                    description=route_data.get('description', ''),
                    clinical_use=route_data.get('clinical_use', ''),
                    reference_metrics=route_data.get('reference_metrics', {})
                )

                self.routes.append(route)

                # Identifier fallback (priority = 1, no required tags)
                if route.priority == 1 and not route.required_tags:
                    self.fallback_model = route

            # Trier routes par priorité (descending)
            self.routes.sort(key=lambda r: r.priority, reverse=True)

            # Routing config global
            self.routing_config = config.get('routing_config', {})

            logger.info(f"Loaded {len(self.routes)} model routes from {self.config_path}")
            if self.fallback_model:
                logger.info(f"Fallback model: {self.fallback_model.model_name}")

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in configuration: {e}")

    def route(self, tags: Dict[str, Optional[str]]) -> ModelRoute:
        """
        Route une lame vers le modèle approprié.

        Stratégie:
        1. Recherche exacte (tous les tags matchent)
        2. Recherche partielle (organ + stain minimum)
        3. Fallback vers modèle générique

        Args:
            tags: {"organ": "prostate", "stain": "H&E", "marker": None, "task": "grading"}

        Returns:
            ModelRoute: Route vers modèle spécialisé ou fallback

        Examples:
            >>> router = TagRouter("config/ml_routes.yaml")
            >>> tags = {"organ": "prostate", "stain": "H&E", "task": "grading"}
            >>> route = router.route(tags)
            >>> print(route.model_name)
            "Gleason Grading Model"

            >>> tags = {"organ": "unknown", "stain": "H&E"}
            >>> route = router.route(tags)
            >>> print(route.model_name)
            "Generic Tumor Detection"  # Fallback
        """
        # Clean tags (remove None values)
        tags = {k: v for k, v in tags.items() if v is not None}

        logger.info(f"Routing tags: {tags}")

        # 1. Recherche exacte (tous les tags matchent)
        exact_matches = self._find_exact_matches(tags)
        if exact_matches:
            best_route = self._select_best_route(exact_matches)
            logger.info(f"Exact match found: {best_route.model_name} (priority {best_route.priority})")
            return best_route

        # 2. Recherche partielle (organ + stain minimum)
        partial_matches = self._find_partial_matches(tags)
        if partial_matches:
            best_route = self._select_best_route(partial_matches)
            logger.info(f"Partial match found: {best_route.model_name} (priority {best_route.priority})")
            return best_route

        # 3. Fallback vers modèle générique
        if self.fallback_model:
            logger.warning(f"No specific model found, using fallback: {self.fallback_model.model_name}")
            return self.fallback_model

        # 4. Aucun modèle disponible (ne devrait jamais arriver si config correcte)
        raise ValueError("No model found for tags and no fallback configured")

    def _find_exact_matches(self, tags: Dict[str, str]) -> List[ModelRoute]:
        """
        Match exact sur tous les tags.

        Args:
            tags: Tags de la slide

        Returns:
            List de routes qui matchent exactement
        """
        matches = []
        for route in self.routes:
            if self._tags_match(route.required_tags, tags, exact=True):
                matches.append(route)
        return matches

    def _find_partial_matches(self, tags: Dict[str, str]) -> List[ModelRoute]:
        """
        Match partiel (organ + stain minimum).

        Args:
            tags: Tags de la slide

        Returns:
            List de routes qui matchent partiellement
        """
        matches = []
        required_keys = ["organ", "stain"]

        for route in self.routes:
            # Skip fallback (pas de required tags)
            if not route.required_tags:
                continue

            # Vérifier si organ + stain matchent
            if all(route.required_tags.get(k) == tags.get(k) for k in required_keys if k in route.required_tags):
                matches.append(route)

        return matches

    def _tags_match(self, required_tags: Dict[str, str], provided_tags: Dict[str, str], exact: bool = False) -> bool:
        """
        Vérifie si tags fournis matchent tags requis.

        Args:
            required_tags: Tags requis par le modèle
            provided_tags: Tags fournis par la slide
            exact: Si True, tous les tags doivent matcher exactement

        Returns:
            True si match, False sinon
        """
        if not required_tags:  # Fallback model (match tout)
            return True

        if exact:
            # Tous les required tags doivent être présents et identiques
            for key, value in required_tags.items():
                if provided_tags.get(key) != value:
                    return False
            return True
        else:
            # Au moins quelques tags doivent matcher
            matching_count = sum(1 for k, v in required_tags.items() if provided_tags.get(k) == v)
            return matching_count >= 2  # Au moins 2 tags matchent

    def _select_best_route(self, matches: List[ModelRoute]) -> ModelRoute:
        """
        Sélectionne le meilleur match par priorité.

        Args:
            matches: List de routes qui matchent

        Returns:
            Route avec la plus haute priorité
        """
        if not matches:
            raise ValueError("No matches to select from")

        # Déjà triées par priorité dans __init__, prendre le premier
        return max(matches, key=lambda r: r.priority)

    def get_all_routes(self) -> List[ModelRoute]:
        """
        Retourne toutes les routes configurées.

        Returns:
            List de toutes les routes
        """
        return self.routes

    def get_route_by_model_id(self, model_id: str) -> Optional[ModelRoute]:
        """
        Récupère route par model_id.

        Args:
            model_id: ID du modèle

        Returns:
            ModelRoute si trouvé, None sinon
        """
        for route in self.routes:
            if route.model_id == model_id:
                return route
        return None

    def reload_configuration(self):
        """
        Recharge configuration depuis fichier (hot reload).

        Utile si configuration modifiée sans redémarrer service.
        """
        logger.info("Reloading routing configuration...")
        self.routes = []
        self.fallback_model = None
        self._load_configuration()
        logger.info("Configuration reloaded successfully")


# ============================================================================
# STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Test routing
    print("\n" + "="*80)
    print("TAG ROUTER - TESTS")
    print("="*80 + "\n")

    # Initialize router
    try:
        router = TagRouter("../../config/ml_routes.yaml")
    except FileNotFoundError:
        print("Configuration file not found - creating mock router")
        # Test avec données mockées
        router = TagRouter.__new__(TagRouter)
        router.routes = [
            ModelRoute(
                model_id="gleason_v2",
                model_name="Gleason Grading",
                model_version="2.0",
                model_path="models:/gleason/prod",
                priority=100,
                min_confidence=0.85,
                task_type="grading",
                required_tags={"organ": "prostate", "stain": "H&E", "task": "grading"}
            ),
            ModelRoute(
                model_id="generic",
                model_name="Generic Detection",
                model_version="1.0",
                model_path="models:/generic/prod",
                priority=1,
                min_confidence=0.75,
                task_type="detection",
                required_tags={}
            )
        ]
        router.fallback_model = router.routes[1]

    # Test cases
    test_cases = [
        {
            "name": "Prostate H&E Grading",
            "tags": {"organ": "prostate", "stain": "H&E", "task": "grading"}
        },
        {
            "name": "Sein Ki-67 (partial match)",
            "tags": {"organ": "sein", "stain": "IHC", "marker": "Ki-67"}
        },
        {
            "name": "Unknown organ (fallback)",
            "tags": {"organ": "unknown", "stain": "H&E"}
        }
    ]

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        print(f"Tags: {test['tags']}")

        try:
            route = router.route(test['tags'])
            print(f"  → Routed to: {route.model_name} (v{route.model_version})")
            print(f"    Model ID: {route.model_id}")
            print(f"    Priority: {route.priority}")
            print(f"    Min confidence: {route.min_confidence}")
        except Exception as e:
            print(f"  → ERROR: {e}")

    print("\n" + "="*80 + "\n")
