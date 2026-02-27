"""
GenerationPipeline: Orchestrates AI video generation for a recommendation feed.

Key design decisions:
  1. CLUSTER-BASED, not per-user — generate for user archetypes, not individuals.
     One generation serves all users in the cluster. This makes GPU cost tractable.

  2. PREDICTIVE, not reactive — generate content BEFORE users need it.
     The pipeline runs in the background, keeping each cluster's content pool filled.

  3. HYBRID blending — mix generated content with curated content.
     Start at 15% generated, dial up as quality improves. The recommender is
     unaware of the distinction; it scores all videos the same way.

  4. BUDGET-CONTROLLED — each cluster has a generation budget per hour.
     Prevents runaway cost. High-engagement clusters get priority.

  5. GRACEFUL FALLBACK — if generation fails or is disabled, the feed works
     identically to before. No single point of failure.
"""

import os
import time
import uuid
import logging
import threading
import numpy as np
from collections import defaultdict
from dataclasses import dataclass, field

from .config import GenerationConfig
from .interest_profiler import InterestProfiler, InterestProfile
from .prompt_composer import PromptComposer, GenerationPrompt
from .providers import GenerationProvider, GenerationResult, create_provider

logger = logging.getLogger(__name__)


@dataclass
class GenerationJob:
    job_id: str
    prompt: GenerationPrompt
    cluster_id: int
    status: str = "queued"       # "queued" | "running" | "completed" | "failed"
    created_at: float = 0.0
    completed_at: float = 0.0
    result: GenerationResult = None
    priority: float = 0.0        # higher = more important

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


@dataclass
class ClusterState:
    cluster_id: int
    user_ids: list = field(default_factory=list)
    centroid_profile: InterestProfile = None
    generated_video_ids: list = field(default_factory=list)
    generation_count_this_hour: int = 0
    hour_started: float = 0.0
    engagement_score: float = 0.0  # average engagement of users in this cluster


class GenerationPipeline:
    """
    Main orchestrator for AI video generation.

    Usage:
        pipeline = GenerationPipeline(config, videos_dir)
        pipeline.initialize(users_db, videos_db)

        # In the recommendation loop:
        generated = pipeline.get_generated_for_user(user_id, n=2)

        # Background tick (call periodically):
        pipeline.tick(users_db, videos_db)
    """

    def __init__(self, config: GenerationConfig, videos_dir: str):
        self.config = config
        self.videos_dir = videos_dir

        self.profiler = InterestProfiler()
        self.composer = PromptComposer(config)
        self.provider: GenerationProvider = create_provider(
            config.provider, videos_dir, **config.provider_config
        )

        self.clusters: dict[int, ClusterState] = {}
        self.job_queue: list[GenerationJob] = []
        self.completed_jobs: list[GenerationJob] = []
        self.generated_videos: dict[str, dict] = {}  # video_id -> video data

        self._interaction_count = 0
        self._lock = threading.Lock()
        self._initialized = False

    def initialize(self, users_db: dict, videos_db: dict):
        """Build initial user clusters from existing data."""
        if not self.config.enabled:
            return

        profiles = []
        for uid in users_db:
            p = self.profiler.build_profile(uid, users_db, videos_db)
            if not p.is_cold_start():
                profiles.append(p)

        if profiles:
            self._cluster_users(profiles)
            logger.info(
                f"Generation pipeline initialized: {len(self.clusters)} clusters, "
                f"provider={self.provider.name}, available={self.provider.is_available()}"
            )

        self._initialized = True

    def tick(self, users_db: dict, videos_db: dict):
        """
        Background tick — call periodically (e.g., every 30s or on interaction).
        Re-clusters if needed, checks pool levels, enqueues generation jobs.
        """
        if not self.config.enabled:
            return

        self._interaction_count += 1

        # Re-cluster periodically
        if self._interaction_count % self.config.recluster_interval == 0:
            profiles = [
                self.profiler.build_profile(uid, users_db, videos_db)
                for uid in users_db
                if not self.profiler.build_profile(uid, users_db, videos_db).is_cold_start()
            ]
            if profiles:
                self._cluster_users(profiles)

        # Check each cluster's pool level and enqueue if needed
        for cluster_id, state in self.clusters.items():
            pool_size = len(state.generated_video_ids)
            if pool_size < self.config.cluster_pool_target:
                if self._has_budget(cluster_id):
                    self._enqueue_for_cluster(cluster_id, state)

        # Process queue
        self._process_queue()

    def get_generated_for_user(self, user_id: str, users_db: dict, videos_db: dict, n: int = 1) -> list[dict]:
        """
        Get generated videos relevant to this user.
        Returns video dicts ready for the recommender to blend into the feed.
        """
        if not self.config.enabled or not self.generated_videos:
            return []

        profile = self.profiler.build_profile(user_id, users_db, videos_db)
        cluster_id = profile.cluster_id

        # Find videos from this user's cluster
        if cluster_id >= 0 and cluster_id in self.clusters:
            cluster_vids = self.clusters[cluster_id].generated_video_ids
            available = [vid for vid in cluster_vids if vid in self.generated_videos]
        else:
            available = list(self.generated_videos.keys())

        if not available:
            return []

        # Score by relevance to this specific user within the cluster
        scored = []
        for vid in available:
            v = self.generated_videos[vid]
            cat_match = profile.category_distribution.get(v.get("category", ""), 0)
            scored.append((vid, cat_match))
        scored.sort(key=lambda x: x[1], reverse=True)

        return [self.generated_videos[vid] for vid, _ in scored[:n]]

    def get_interest_profile(self, user_id: str, users_db: dict, videos_db: dict) -> dict:
        """Get the interest profile for a user (for API exposure)."""
        profile = self.profiler.build_profile(user_id, users_db, videos_db)
        return profile.to_dict()

    def get_pipeline_status(self) -> dict:
        """Get pipeline status for monitoring/debugging."""
        return {
            "enabled": self.config.enabled,
            "provider": self.provider.name,
            "provider_available": self.provider.is_available(),
            "num_clusters": len(self.clusters),
            "cluster_sizes": {
                cid: len(s.user_ids) for cid, s in self.clusters.items()
            },
            "generated_video_count": len(self.generated_videos),
            "queue_length": len([j for j in self.job_queue if j.status == "queued"]),
            "completed_jobs": len(self.completed_jobs),
            "config": {
                "generated_content_ratio": self.config.generated_content_ratio,
                "cluster_pool_target": self.config.cluster_pool_target,
                "budget_per_cluster_per_hour": self.config.budget_per_cluster_per_hour,
            },
        }

    def compose_prompt_preview(self, user_id: str, users_db: dict, videos_db: dict) -> dict:
        """Preview what prompt would be generated for a user (without running generation)."""
        profile = self.profiler.build_profile(user_id, users_db, videos_db)
        prompt = self.composer.compose(profile)
        return {
            "profile": profile.to_dict(),
            "prompt": prompt.to_dict(),
        }

    # --- Internal methods ---

    def _cluster_users(self, profiles: list[InterestProfile]):
        """
        Cluster users by interest similarity.
        Uses simple k-means on category distribution vectors.
        """
        n = len(profiles)
        k = min(self.config.num_user_clusters, n)
        if k == 0:
            return

        # Build feature vectors from category distributions
        all_cats = set()
        for p in profiles:
            all_cats.update(p.category_distribution.keys())
        all_cats = sorted(all_cats)

        vectors = np.zeros((n, len(all_cats)))
        for i, p in enumerate(profiles):
            for j, cat in enumerate(all_cats):
                vectors[i, j] = p.category_distribution.get(cat, 0)

        # Simple k-means (avoid sklearn dependency in this module)
        labels = self._kmeans(vectors, k, max_iter=20)

        # Build cluster states
        new_clusters = {}
        for i, profile in enumerate(profiles):
            cid = int(labels[i])
            profile.cluster_id = cid
            if cid not in new_clusters:
                new_clusters[cid] = ClusterState(cluster_id=cid)
            new_clusters[cid].user_ids.append(profile.user_id)

        # Compute centroid profiles for each cluster
        for cid, state in new_clusters.items():
            cluster_profiles = [p for p in profiles if p.cluster_id == cid]
            state.centroid_profile = cluster_profiles[0] if cluster_profiles else None
            # Carry over existing generated videos
            if cid in self.clusters:
                state.generated_video_ids = self.clusters[cid].generated_video_ids
                state.generation_count_this_hour = self.clusters[cid].generation_count_this_hour
                state.hour_started = self.clusters[cid].hour_started

        self.clusters = new_clusters

    def _kmeans(self, X: np.ndarray, k: int, max_iter: int = 20) -> np.ndarray:
        """Minimal k-means implementation."""
        n = X.shape[0]
        indices = np.random.choice(n, k, replace=False)
        centroids = X[indices].copy()
        labels = np.zeros(n, dtype=int)

        for _ in range(max_iter):
            # Assign
            for i in range(n):
                dists = np.linalg.norm(X[i] - centroids, axis=1)
                labels[i] = np.argmin(dists)
            # Update
            new_centroids = np.zeros_like(centroids)
            for j in range(k):
                members = X[labels == j]
                if len(members) > 0:
                    new_centroids[j] = members.mean(axis=0)
                else:
                    new_centroids[j] = centroids[j]
            if np.allclose(centroids, new_centroids):
                break
            centroids = new_centroids

        return labels

    def _has_budget(self, cluster_id: int) -> bool:
        state = self.clusters.get(cluster_id)
        if not state:
            return False
        now = time.time()
        if now - state.hour_started > 3600:
            state.generation_count_this_hour = 0
            state.hour_started = now
        return state.generation_count_this_hour < self.config.budget_per_cluster_per_hour

    def _enqueue_for_cluster(self, cluster_id: int, state: ClusterState):
        """Create a generation job for a cluster."""
        if not state.centroid_profile:
            return

        # Don't double-enqueue
        pending = [j for j in self.job_queue if j.cluster_id == cluster_id and j.status == "queued"]
        if pending:
            return

        cluster_profiles = [
            self.profiler.get_cached_profile(uid)
            for uid in state.user_ids
            if self.profiler.get_cached_profile(uid)
        ]
        prompt = self.composer.compose_for_cluster(
            cluster_profiles if cluster_profiles else [state.centroid_profile],
            cluster_id,
        )

        job = GenerationJob(
            job_id=f"job_{uuid.uuid4().hex[:8]}",
            prompt=prompt,
            cluster_id=cluster_id,
            priority=len(state.user_ids),  # more users = higher priority
        )
        self.job_queue.append(job)

    def _process_queue(self):
        """Process the next job in the queue."""
        pending = [j for j in self.job_queue if j.status == "queued"]
        if not pending:
            return

        running = [j for j in self.job_queue if j.status == "running"]
        if len(running) >= self.config.max_concurrent_jobs:
            return

        # Pick highest priority
        pending.sort(key=lambda j: j.priority, reverse=True)
        job = pending[0]

        job.status = "running"
        result = self.provider.generate(job.prompt)
        job.result = result
        job.completed_at = time.time()

        if result.success:
            job.status = "completed"
            self._register_generated_video(job)
            state = self.clusters.get(job.cluster_id)
            if state:
                state.generation_count_this_hour += 1
        else:
            job.status = "failed"

        self.completed_jobs.append(job)
        self.job_queue.remove(job)

    def _register_generated_video(self, job: GenerationJob):
        """Register a generated video in the system."""
        result = job.result
        prompt = job.prompt

        video_data = {
            "video_id": result.video_id,
            "filename": os.path.basename(result.video_path) if result.video_path else "",
            "url": f"/videos/{os.path.basename(result.video_path)}" if result.video_path else "",
            "category": prompt.category,
            "description": f"AI generated: {prompt.scene[:80]}",
            "tags": prompt.tags,
            "duration": prompt.duration,
            "created_at": time.time(),
            "is_generated": True,
            "generation_prompt": prompt.to_dict(),
            "source_cluster": job.cluster_id,
            "provider": result.provider,
        }

        self.generated_videos[result.video_id] = video_data

        if job.cluster_id in self.clusters:
            self.clusters[job.cluster_id].generated_video_ids.append(result.video_id)
