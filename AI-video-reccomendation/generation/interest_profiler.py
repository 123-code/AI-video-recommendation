"""
InterestProfiler: Converts raw user interaction data into structured interest profiles.

This is the core intelligence for generation — understanding WHAT to generate.
The profiler extracts:
  - Category distribution (weighted by recency and interaction strength)
  - Visual embedding centroid (what visuals the user gravitates toward)
  - Engagement depth (passive scroller vs. active engager)
  - Novelty-seeking score (prefers diverse content vs. familiar patterns)
  - Temporal patterns (what they engage with and when)

The profile is model-agnostic — any generation provider can use it.
"""

import math
import time
import numpy as np
from dataclasses import dataclass, field
from collections import defaultdict


INTERACTION_WEIGHTS = {
    "like": 3.0,
    "comment": 4.0,
    "share": 5.0,
    "watch_time": 1.0,
    "view": 0.2,
}

HALF_LIFE_HOURS = 72  # interest signal decays by half every 72 hours


@dataclass
class InterestProfile:
    user_id: str
    category_distribution: dict = field(default_factory=dict)  # category -> score [0,1]
    top_categories: list = field(default_factory=list)          # ranked list
    embedding_centroid: np.ndarray = field(default_factory=lambda: np.zeros(512))
    engagement_depth: float = 0.0    # 0 = passive, 1 = deeply engaged
    novelty_score: float = 0.5       # 0 = wants familiar, 1 = wants novel
    preferred_motion: str = "medium"  # "slow" | "medium" | "fast"
    preferred_mood: str = "neutral"   # "calm" | "neutral" | "energetic"
    content_maturity: float = 0.0    # how many interactions this profile is based on
    cluster_id: int = -1             # assigned user cluster (-1 = unclustered)

    def is_cold_start(self) -> bool:
        return self.content_maturity < 5

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "category_distribution": self.category_distribution,
            "top_categories": self.top_categories,
            "engagement_depth": round(self.engagement_depth, 3),
            "novelty_score": round(self.novelty_score, 3),
            "preferred_motion": self.preferred_motion,
            "preferred_mood": self.preferred_mood,
            "content_maturity": round(self.content_maturity, 1),
            "cluster_id": self.cluster_id,
        }


class InterestProfiler:
    def __init__(self, embedding_dim: int = 512):
        self.embedding_dim = embedding_dim
        self._profiles_cache: dict[str, InterestProfile] = {}

    def build_profile(self, user_id: str, users_db: dict, videos_db: dict) -> InterestProfile:
        """Build a complete interest profile from raw data."""
        user = users_db.get(user_id)
        if not user:
            return InterestProfile(user_id=user_id)

        profile = InterestProfile(user_id=user_id)

        liked_videos = user.get("liked_videos", [])
        watched_videos = user.get("watched_videos", [])
        category_interests = user.get("category_interests", {})

        all_interacted = set(liked_videos) | set(watched_videos)
        profile.content_maturity = len(all_interacted)

        if profile.is_cold_start():
            profile.category_distribution = {cat: 1.0 / max(len(category_interests), 1)
                                              for cat in category_interests}
            profile.top_categories = list(category_interests.keys())[:3]
            return profile

        # Category distribution with temporal decay
        cat_scores = self._compute_category_scores(user, videos_db)
        total = sum(cat_scores.values()) or 1.0
        profile.category_distribution = {k: v / total for k, v in cat_scores.items()}
        profile.top_categories = sorted(cat_scores.keys(), key=cat_scores.get, reverse=True)[:5]

        # Embedding centroid from liked videos
        profile.embedding_centroid = self._compute_embedding_centroid(liked_videos, videos_db)

        # Engagement depth: ratio of active interactions (like/comment/share) to passive (view)
        profile.engagement_depth = self._compute_engagement_depth(user, videos_db)

        # Novelty score: how diverse are the categories the user engages with?
        profile.novelty_score = self._compute_novelty_score(cat_scores)

        # Preferred motion/mood inferred from category preferences
        profile.preferred_motion = self._infer_motion_preference(profile.top_categories)
        profile.preferred_mood = self._infer_mood_preference(profile.top_categories)

        self._profiles_cache[user_id] = profile
        return profile

    def _compute_category_scores(self, user: dict, videos_db: dict) -> dict:
        """Weight category interests by interaction type and recency."""
        scores = defaultdict(float)
        now = time.time()

        liked = set(user.get("liked_videos", []))
        watched = set(user.get("watched_videos", []))

        for vid in liked | watched:
            v = videos_db.get(vid)
            if not v:
                continue
            cat = v.get("category", "Unknown")
            age_hours = (now - v.get("created_at", now)) / 3600
            decay = math.exp(-math.log(2) * age_hours / HALF_LIFE_HOURS)

            weight = INTERACTION_WEIGHTS["view"]
            if vid in liked:
                weight = INTERACTION_WEIGHTS["like"]
            scores[cat] += weight * decay

        return dict(scores)

    def _compute_embedding_centroid(self, liked_videos: list, videos_db: dict) -> np.ndarray:
        """Weighted average of liked video embeddings."""
        embeddings = []
        for vid in liked_videos:
            v = videos_db.get(vid)
            if v and v.get("embedding") is not None:
                embeddings.append(v["embedding"])

        if not embeddings:
            return np.zeros(self.embedding_dim)

        centroid = np.mean(embeddings, axis=0)
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        return centroid

    def _compute_engagement_depth(self, user: dict, videos_db: dict) -> float:
        """0 = passive scroller, 1 = actively engages."""
        liked = len(user.get("liked_videos", []))
        watched = len(user.get("watched_videos", []))
        if watched == 0:
            return 0.0
        ratio = liked / watched
        return min(ratio * 2, 1.0)  # normalize: liking 50%+ of watched = max engagement

    def _compute_novelty_score(self, cat_scores: dict) -> float:
        """Shannon entropy of category distribution, normalized."""
        if not cat_scores:
            return 0.5
        total = sum(cat_scores.values())
        if total == 0:
            return 0.5
        probs = [v / total for v in cat_scores.values() if v > 0]
        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(max(len(probs), 1)) or 1
        return min(entropy / max_entropy, 1.0)

    def _infer_motion_preference(self, top_categories: list) -> str:
        slow_cats = {"Nature", "Landscape", "Ocean", "ASMR", "Gradient"}
        fast_cats = {"Urban", "Dance", "Technology", "Psychedelic", "Generative"}
        slow_count = sum(1 for c in top_categories if c in slow_cats)
        fast_count = sum(1 for c in top_categories if c in fast_cats)
        if slow_count > fast_count:
            return "slow"
        if fast_count > slow_count:
            return "fast"
        return "medium"

    def _infer_mood_preference(self, top_categories: list) -> str:
        calm_cats = {"Nature", "Landscape", "Ocean", "ASMR", "Gradient"}
        energetic_cats = {"Urban", "Dance", "Psychedelic", "Retro", "Comedy"}
        calm = sum(1 for c in top_categories if c in calm_cats)
        energetic = sum(1 for c in top_categories if c in energetic_cats)
        if calm > energetic:
            return "calm"
        if energetic > calm:
            return "energetic"
        return "neutral"

    def get_cached_profile(self, user_id: str) -> InterestProfile | None:
        return self._profiles_cache.get(user_id)
