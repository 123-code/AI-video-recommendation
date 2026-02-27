"""
Pipeline configuration.

Tuning these values controls the balance between generated and curated content,
how aggressively the system pre-generates, and how generation budget is allocated.
"""

from dataclasses import dataclass, field


@dataclass
class GenerationConfig:
    enabled: bool = False

    # Provider selection: "stub" | "open_sora" | "replicate" | "local_diffusion"
    provider: str = "stub"

    # How many videos to keep pre-generated per user cluster
    cluster_pool_target: int = 10

    # Max concurrent generation jobs
    max_concurrent_jobs: int = 4

    # What fraction of the feed should be generated content (0.0 - 1.0)
    # Start low, increase as generation quality improves
    generated_content_ratio: float = 0.15

    # Number of user clusters for archetype-based generation.
    # One generation serves all users in the cluster, not individual users.
    num_user_clusters: int = 8

    # Generation budget per cluster per hour (prevents runaway cost)
    budget_per_cluster_per_hour: int = 5

    # Re-cluster users every N interactions
    recluster_interval: int = 500

    # Min interactions before a user contributes to clustering
    min_interactions_for_clustering: int = 5

    # Target video duration range for generation (seconds)
    min_duration: float = 3.0
    max_duration: float = 8.0

    # Target resolution
    width: int = 480
    height: int = 854

    # Provider-specific config (passed through to the provider)
    provider_config: dict = field(default_factory=dict)
