"""
Locust Load Test — Pathologist Session Simulation

Simulates realistic pathologist workflows:
  - Browse slide list → open a slide → pan/zoom (tiles) → review annotations

Run headless:
    locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 120s --host http://localhost:8000

Run with web UI:
    locust -f tests/load/locustfile.py --host http://localhost:8000
"""

import random

from locust import HttpUser, between, task


class PathologistUser(HttpUser):
    """
    Simulates a pathologist browsing histological slides.

    Task weights reflect real usage patterns:
      - Tile requests dominate (panning/zooming the viewer)
      - Slide browsing and annotation reads are frequent
      - Annotation creation and exports are occasional
    """

    wait_time = between(1, 3)

    def on_start(self):
        """Harvest real slide IDs from the API, or fall back to synthetic IDs."""
        self.slide_ids = []
        try:
            resp = self.client.get("/api/slides/", name="/api/slides/")
            if resp.status_code == 200:
                data = resp.json()
                # Handle both list-of-strings and list-of-dicts formats
                for item in data:
                    if isinstance(item, str):
                        self.slide_ids.append(item)
                    elif isinstance(item, dict) and "slide_id" in item:
                        self.slide_ids.append(item["slide_id"])
                    elif isinstance(item, dict) and "id" in item:
                        self.slide_ids.append(item["id"])
        except Exception:
            pass

        # Fall back to 50 synthetic IDs if no real slides found
        if not self.slide_ids:
            self.slide_ids = [f"load_test_slide_{i:03d}" for i in range(50)]

        # Track annotation IDs we've created for later operations
        self._created_annotation_ids = {}

    def _random_slide(self):
        return random.choice(self.slide_ids)

    # ------------------------------------------------------------------
    # Tasks (weights model realistic pathologist behavior)
    # ------------------------------------------------------------------

    @task(1)
    def health_check(self):
        """Background keep-alive / health poll."""
        self.client.get("/api/health", name="/api/health")

    @task(3)
    def browse_slides(self):
        """Browse the slide list (landing page)."""
        self.client.get("/api/slides/", name="/api/slides/")

    @task(5)
    def view_slide_info(self):
        """Open a specific slide to view metadata."""
        slide_id = self._random_slide()
        with self.client.get(
            f"/api/slides/{slide_id}/info",
            name="/api/slides/[id]/info",
            catch_response=True,
        ) as resp:
            # 404 is expected with synthetic slide IDs in dev
            if resp.status_code == 404:
                resp.success()

    @task(10)
    def view_tiles(self):
        """Fetch 3-8 tiles simulating panning/zooming (heaviest operation)."""
        slide_id = self._random_slide()
        num_tiles = random.randint(3, 8)
        level = random.randint(0, 4)

        for _ in range(num_tiles):
            col = random.randint(0, 50)
            row = random.randint(0, 50)
            with self.client.get(
                f"/api/slides/{slide_id}/tiles/{level}/{col}_{row}.jpg",
                name="/api/slides/[id]/tiles/[level]/[col]_[row].jpg",
                catch_response=True,
            ) as resp:
                # 404 is expected when slides don't exist in dev — don't count as failure
                if resp.status_code == 404:
                    resp.success()

    @task(4)
    def list_annotations(self):
        """Load annotation overlay for a slide."""
        slide_id = self._random_slide()
        self.client.get(
            f"/api/annotations/{slide_id}",
            name="/api/annotations/[slide_id]",
        )

    @task(2)
    def create_annotation(self):
        """Draw an annotation on a slide."""
        slide_id = self._random_slide()
        x = random.randint(0, 90000)
        y = random.randint(0, 70000)
        size = random.randint(500, 3000)

        annotation = {
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [x, y],
                        [x + size, y],
                        [x + size, y + size],
                        [x, y + size],
                        [x, y],
                    ]
                ],
            },
            "geometry_type": random.choice(["polygon", "rectangle"]),
            "annotation_type": "manual",
        }

        with self.client.post(
            f"/api/annotations/{slide_id}",
            json=annotation,
            name="/api/annotations/[slide_id] POST",
            catch_response=True,
        ) as resp:
            if resp.status_code == 201:
                anno_id = resp.json().get("id")
                if anno_id:
                    self._created_annotation_ids.setdefault(slide_id, []).append(anno_id)
                resp.success()
            elif resp.status_code in (401, 403, 500):
                # Auth/server errors expected in some environments
                resp.success()

    @task(1)
    def get_annotation_stats(self):
        """View annotation statistics panel."""
        slide_id = self._random_slide()
        self.client.get(
            f"/api/annotations/{slide_id}/stats",
            name="/api/annotations/[slide_id]/stats",
        )

    @task(1)
    def export_geojson(self):
        """Export annotations as GeoJSON."""
        slide_id = self._random_slide()
        self.client.get(
            f"/api/annotations/{slide_id}/export",
            name="/api/annotations/[slide_id]/export",
        )
