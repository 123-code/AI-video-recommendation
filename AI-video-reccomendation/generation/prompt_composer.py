"""
PromptComposer: Converts InterestProfiles into structured generation prompts.

Two-layer design:
  1. Structured prompt (JSON) — model-agnostic, describes what to generate
  2. Text prompt — provider-specific natural language (each provider translates differently)

The structured format means switching from Open Sora to Replicate to a future model
only requires writing a new translator, not changing the prompting logic.
"""

import random
from dataclasses import dataclass, field
from .interest_profiler import InterestProfile


@dataclass
class GenerationPrompt:
    """Model-agnostic structured prompt for video generation."""
    prompt_id: str = ""
    scene: str = ""
    style: str = ""
    color_palette: list = field(default_factory=list)
    motion: str = "medium"        # "static" | "slow" | "medium" | "fast" | "dynamic"
    mood: str = "neutral"         # "calm" | "neutral" | "energetic" | "dramatic" | "dreamy"
    camera: str = "static"        # "static" | "slow_pan" | "tracking" | "aerial" | "zoom_in"
    lighting: str = "natural"     # "natural" | "golden_hour" | "neon" | "dramatic" | "soft"
    duration: float = 5.0
    width: int = 480
    height: int = 854
    negative_prompt: str = "blurry, low quality, distorted, watermark, text overlay"
    source_profile: str = ""      # user_id or cluster_id that triggered this
    category: str = ""
    tags: list = field(default_factory=list)

    def to_text(self) -> str:
        """Convert to a natural language prompt suitable for most diffusion models."""
        parts = [self.scene]
        if self.style:
            parts.append(self.style)
        if self.color_palette:
            parts.append(f"{', '.join(self.color_palette)} color palette")
        parts.append(f"{self.motion} motion")
        parts.append(f"{self.mood} mood")
        if self.camera != "static":
            parts.append(f"{self.camera.replace('_', ' ')} camera")
        parts.append(f"{self.lighting} lighting")
        return ", ".join(parts)

    def to_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "text_prompt": self.to_text(),
            "scene": self.scene,
            "style": self.style,
            "color_palette": self.color_palette,
            "motion": self.motion,
            "mood": self.mood,
            "camera": self.camera,
            "lighting": self.lighting,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "negative_prompt": self.negative_prompt,
            "source_profile": self.source_profile,
            "category": self.category,
            "tags": self.tags,
        }


# Scene templates by category — each is a callable that returns a scene description
# with randomized variety to avoid repetitive content
SCENE_TEMPLATES = {
    "Nature": [
        "lush green forest with sunlight filtering through the canopy, morning dew on leaves",
        "wildflowers swaying in a gentle breeze on a mountain meadow",
        "ancient tree with twisted roots in a misty woodland",
        "crystal clear stream flowing over smooth stones in a forest",
        "dense bamboo grove with light and shadow patterns",
    ],
    "Ocean": [
        "turquoise ocean waves crashing on a sandy beach at sunset",
        "underwater coral reef with sunlight rays piercing the water",
        "aerial view of deep blue ocean with white wave patterns",
        "bioluminescent waves on a dark beach at night",
        "massive wave curling in slow motion, glassy water surface",
    ],
    "Urban": [
        "neon-lit city street at night with reflections on wet pavement",
        "aerial timelapse of city traffic flowing through intersections",
        "moody alleyway with steam rising from grates, cinematic lighting",
        "modern skyscraper facade reflecting clouds and sunset",
        "busy subway station with motion blur of passing trains",
    ],
    "Fractal": [
        "infinite fractal zoom into a Mandelbrot set, vivid colors morphing",
        "organic fractal patterns resembling alien coral growth",
        "geometric fractal tessellation expanding outward in all directions",
        "Julia set fractal animation with spiraling arms",
        "fractal landscape resembling impossible mountains and valleys",
    ],
    "Abstract": [
        "fluid ink dropping into water creating organic abstract patterns",
        "geometric shapes morphing and tessellating in 3D space",
        "smoke tendrils dancing in colored light beams",
        "abstract paint splashes frozen in mid-air, vibrant colors",
        "minimal abstract composition with floating spheres and light",
    ],
    "Psychedelic": [
        "kaleidoscopic pattern of shifting colors and symmetrical shapes",
        "hypnotic spiral tunnel with rainbow chromatic aberration",
        "morphing organic shapes with iridescent surfaces",
        "visual music synesthesia, sound waves becoming color patterns",
        "infinite recursive mirror tunnel with neon edges",
    ],
    "Landscape": [
        "dramatic mountain range at golden hour with long shadows",
        "vast desert dunes with wind creating sand ripples",
        "northern lights dancing over a frozen lake in Iceland",
        "terraced rice fields in morning mist, Southeast Asia",
        "volcanic landscape with glowing lava flows at twilight",
    ],
    "Cinematic": [
        "slow motion shot of rain drops hitting a still water surface",
        "dolly zoom through an empty hallway with dramatic shadows",
        "extreme close-up of an eye reflecting a landscape",
        "time-lapse of clouds racing over a cityscape",
        "chiaroscuro portrait lighting with dramatic shadows",
    ],
    "Space": [
        "nebula cloud with newborn stars glowing in vivid colors",
        "Earth rising over the lunar horizon, deep space background",
        "asteroid field drifting through deep space with distant galaxies",
        "solar flare erupting from the sun's surface in extreme detail",
        "rings of Saturn with ice particles catching sunlight",
    ],
    "Generative": [
        "particle system simulation creating emergent patterns",
        "cellular automata evolving complex structures from simple rules",
        "reaction-diffusion patterns forming organic textures",
        "flocking simulation with thousands of particles moving as one",
        "neural network visualization with activating nodes and connections",
    ],
    "Gradient": [
        "smooth gradient transition between warm sunset colors",
        "aurora borealis color gradient shifting across the sky",
        "deep ocean gradient from surface turquoise to abyssal black",
        "holographic iridescent surface with shifting gradient colors",
        "thermal gradient visualization from cool blue to hot white",
    ],
    "Satisfying": [
        "perfect symmetrical pattern being drawn by a precision machine",
        "viscous fluid pouring in a satisfying spiral pattern",
        "dominos falling in an elaborate chain reaction",
        "paint mixing in slow motion creating marbled patterns",
        "kinetic sand being cut and shaped with sharp precision",
    ],
}

STYLE_MAP = {
    "calm": ["soft focus", "dreamy", "ethereal", "gentle", "serene"],
    "neutral": ["cinematic", "clean", "balanced", "natural", "polished"],
    "energetic": ["dynamic", "bold", "high contrast", "vivid", "punchy"],
}

COLOR_PALETTES = {
    "calm": [
        ["soft blue", "lavender", "cream"],
        ["sage green", "warm white", "light gold"],
        ["pale pink", "dusty rose", "ivory"],
    ],
    "neutral": [
        ["deep blue", "warm orange", "neutral gray"],
        ["forest green", "burnt sienna", "cream"],
        ["slate blue", "coral", "sand"],
    ],
    "energetic": [
        ["neon pink", "electric blue", "hot yellow"],
        ["vivid red", "bright cyan", "white"],
        ["magenta", "lime green", "deep purple"],
    ],
}

CAMERA_MOVEMENTS = {
    "slow": ["static", "slow_pan", "slow_pan"],
    "medium": ["static", "slow_pan", "tracking", "zoom_in"],
    "fast": ["tracking", "aerial", "zoom_in", "tracking"],
}

LIGHTING_MAP = {
    "calm": ["soft", "golden_hour", "natural"],
    "neutral": ["natural", "golden_hour", "dramatic"],
    "energetic": ["neon", "dramatic", "neon"],
}


class PromptComposer:
    def __init__(self, config=None):
        self.config = config
        self._prompt_counter = 0

    def compose(self, profile: InterestProfile) -> GenerationPrompt:
        """Generate a structured prompt from an interest profile."""
        self._prompt_counter += 1

        # Pick category: weighted by profile distribution with some exploration
        category = self._pick_category(profile)

        # Pick scene template for this category
        scene = self._pick_scene(category)

        # Style, colors, motion, mood from profile preferences
        mood = profile.preferred_mood
        style = random.choice(STYLE_MAP.get(mood, STYLE_MAP["neutral"]))
        colors = random.choice(COLOR_PALETTES.get(mood, COLOR_PALETTES["neutral"]))
        motion = profile.preferred_motion
        camera = random.choice(CAMERA_MOVEMENTS.get(motion, CAMERA_MOVEMENTS["medium"]))
        lighting = random.choice(LIGHTING_MAP.get(mood, LIGHTING_MAP["neutral"]))

        # Inject novelty if user has high novelty score
        if profile.novelty_score > 0.7:
            # Mix in an unexpected element
            surprise_cats = [c for c in SCENE_TEMPLATES if c != category]
            if surprise_cats:
                surprise = random.choice(surprise_cats)
                scene += f", with elements of {surprise.lower()}"

        duration = random.uniform(
            self.config.min_duration if self.config else 3.0,
            self.config.max_duration if self.config else 8.0,
        )

        prompt = GenerationPrompt(
            prompt_id=f"gen_{self._prompt_counter}_{category.lower()}",
            scene=scene,
            style=style,
            color_palette=colors,
            motion=motion,
            mood=mood,
            camera=camera,
            lighting=lighting,
            duration=round(duration, 1),
            width=self.config.width if self.config else 480,
            height=self.config.height if self.config else 854,
            source_profile=profile.user_id,
            category=category,
            tags=[f"#{category.lower()}", "#generated", "#foryou", "#ai"],
        )

        return prompt

    def compose_for_cluster(self, profiles: list[InterestProfile], cluster_id: int) -> GenerationPrompt:
        """Compose a prompt that serves a cluster of similar users.
        Finds the centroid of the cluster's preferences."""
        if not profiles:
            return self.compose(InterestProfile(user_id=f"cluster_{cluster_id}"))

        # Aggregate category distributions
        merged_cats = {}
        for p in profiles:
            for cat, score in p.category_distribution.items():
                merged_cats[cat] = merged_cats.get(cat, 0) + score
        total = sum(merged_cats.values()) or 1
        merged_cats = {k: v / total for k, v in merged_cats.items()}

        # Average mood/motion
        moods = [p.preferred_mood for p in profiles]
        motions = [p.preferred_motion for p in profiles]
        mood = max(set(moods), key=moods.count)
        motion = max(set(motions), key=motions.count)

        avg_novelty = sum(p.novelty_score for p in profiles) / len(profiles)

        merged = InterestProfile(
            user_id=f"cluster_{cluster_id}",
            category_distribution=merged_cats,
            top_categories=sorted(merged_cats, key=merged_cats.get, reverse=True)[:5],
            novelty_score=avg_novelty,
            preferred_mood=mood,
            preferred_motion=motion,
            content_maturity=sum(p.content_maturity for p in profiles) / len(profiles),
            cluster_id=cluster_id,
        )
        return self.compose(merged)

    def _pick_category(self, profile: InterestProfile) -> str:
        cats = list(profile.category_distribution.keys())
        weights = list(profile.category_distribution.values())

        if not cats:
            return random.choice(list(SCENE_TEMPLATES.keys()))

        # Add small exploration weight to all known categories
        all_cats = list(SCENE_TEMPLATES.keys())
        explore_weight = 0.05
        for c in all_cats:
            if c not in cats:
                cats.append(c)
                weights.append(explore_weight)

        total = sum(weights)
        weights = [w / total for w in weights]
        return random.choices(cats, weights=weights, k=1)[0]

    def _pick_scene(self, category: str) -> str:
        templates = SCENE_TEMPLATES.get(category, SCENE_TEMPLATES.get("Abstract", [""]))
        return random.choice(templates) if templates else f"beautiful {category.lower()} scene"
