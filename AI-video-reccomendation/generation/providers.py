"""
GenerationProvider: Abstract interface for video generation backends.

The provider pattern means the entire pipeline is model-agnostic.
Switching from Open Sora to Replicate to a local model is a config change.

Each provider implements:
  - generate(prompt) -> GenerationResult
  - is_available() -> bool
  - estimated_time(prompt) -> seconds

Providers:
  - StubProvider: returns existing videos (for development/testing)
  - OpenSoraProvider: skeleton for HuggingFace Open Sora
  - ReplicateProvider: skeleton for Replicate API
  - LocalDiffusionProvider: skeleton for local GPU inference
"""

import os
import time
import random
import uuid
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from .prompt_composer import GenerationPrompt

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    success: bool
    video_path: str = ""
    video_id: str = ""
    duration: float = 0.0
    generation_time: float = 0.0
    prompt: GenerationPrompt = None
    error: str = ""
    provider: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class GenerationProvider(ABC):
    """Base class for all video generation providers."""

    @abstractmethod
    def generate(self, prompt: GenerationPrompt) -> GenerationResult:
        """Generate a video from a structured prompt. Blocking call."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is currently usable."""
        ...

    @abstractmethod
    def estimated_time(self, prompt: GenerationPrompt) -> float:
        """Estimated generation time in seconds."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...


class StubProvider(GenerationProvider):
    """Returns an existing video from the library. For development and fallback."""

    def __init__(self, videos_dir: str):
        self.videos_dir = videos_dir

    @property
    def name(self) -> str:
        return "stub"

    def generate(self, prompt: GenerationPrompt) -> GenerationResult:
        files = [f for f in os.listdir(self.videos_dir)
                 if f.endswith(".mp4") and not f.startswith("demo")]
        if not files:
            return GenerationResult(success=False, error="No videos available", provider=self.name)

        chosen = random.choice(files)
        vid_id = f"generated_{uuid.uuid4().hex[:8]}"
        return GenerationResult(
            success=True,
            video_path=os.path.join(self.videos_dir, chosen),
            video_id=vid_id,
            duration=prompt.duration,
            generation_time=0.01,
            prompt=prompt,
            provider=self.name,
            metadata={"source_file": chosen, "stub": True},
        )

    def is_available(self) -> bool:
        return os.path.exists(self.videos_dir)

    def estimated_time(self, prompt: GenerationPrompt) -> float:
        return 0.01


class OpenSoraProvider(GenerationProvider):
    """
    Open Sora (HuggingFace diffusers) provider.

    Requires: torch, diffusers, GPU with sufficient VRAM.
    When the model is production-ready, implement generate() to:
      1. Load the Open Sora pipeline (cached after first load)
      2. Convert GenerationPrompt.to_text() into model-specific format
      3. Run inference
      4. Save output to videos_dir
    """

    def __init__(self, videos_dir: str, model_id: str = "hpcai-tech/Open-Sora", **kwargs):
        self.videos_dir = videos_dir
        self.model_id = model_id
        self.kwargs = kwargs
        self._pipeline = None

    @property
    def name(self) -> str:
        return "open_sora"

    def generate(self, prompt: GenerationPrompt) -> GenerationResult:
        # When Open Sora is production-ready, this becomes:
        #
        # if self._pipeline is None:
        #     from diffusers import OpenSoraPipeline
        #     self._pipeline = OpenSoraPipeline.from_pretrained(
        #         self.model_id, torch_dtype=torch.float16
        #     ).to("cuda")
        #
        # output = self._pipeline(
        #     prompt=prompt.to_text(),
        #     negative_prompt=prompt.negative_prompt,
        #     num_frames=int(prompt.duration * 24),
        #     height=prompt.height,
        #     width=prompt.width,
        #     guidance_scale=7.5,
        # )
        #
        # video_id = f"generated_{uuid.uuid4().hex[:8]}"
        # out_path = os.path.join(self.videos_dir, f"{video_id}.mp4")
        # export_to_video(output.frames[0], out_path, fps=24)
        #
        # return GenerationResult(success=True, video_path=out_path, ...)

        return GenerationResult(
            success=False,
            error="Open Sora provider not yet implemented — awaiting production-ready model",
            provider=self.name,
        )

    def is_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def estimated_time(self, prompt: GenerationPrompt) -> float:
        return prompt.duration * 30  # ~30s per second of video on A100


class ReplicateProvider(GenerationProvider):
    """
    Replicate API provider for cloud-based generation.

    Requires: REPLICATE_API_TOKEN environment variable.
    When ready, implement generate() to call the Replicate API with
    the model of choice (e.g., minimax/video-01, luma/ray).
    """

    def __init__(self, videos_dir: str, model_version: str = "minimax/video-01", **kwargs):
        self.videos_dir = videos_dir
        self.model_version = model_version
        self.api_token = os.environ.get("REPLICATE_API_TOKEN", "")

    @property
    def name(self) -> str:
        return "replicate"

    def generate(self, prompt: GenerationPrompt) -> GenerationResult:
        # When ready:
        #
        # import replicate
        # output = replicate.run(
        #     self.model_version,
        #     input={
        #         "prompt": prompt.to_text(),
        #         "duration": prompt.duration,
        #         "aspect_ratio": f"{prompt.width}:{prompt.height}",
        #     }
        # )
        #
        # video_id = f"generated_{uuid.uuid4().hex[:8]}"
        # out_path = os.path.join(self.videos_dir, f"{video_id}.mp4")
        # download(output, out_path)
        #
        # return GenerationResult(success=True, video_path=out_path, ...)

        return GenerationResult(
            success=False,
            error="Replicate provider not yet implemented — set REPLICATE_API_TOKEN when ready",
            provider=self.name,
        )

    def is_available(self) -> bool:
        return bool(self.api_token)

    def estimated_time(self, prompt: GenerationPrompt) -> float:
        return prompt.duration * 20


class LocalDiffusionProvider(GenerationProvider):
    """
    Local GPU inference with any diffusers-compatible video model.

    This is the most flexible provider — point it at any HuggingFace model
    that supports text-to-video generation.
    """

    def __init__(self, videos_dir: str, model_id: str = "ali-vilab/text-to-video-ms-1.7b", **kwargs):
        self.videos_dir = videos_dir
        self.model_id = model_id
        self._pipeline = None

    @property
    def name(self) -> str:
        return "local_diffusion"

    def generate(self, prompt: GenerationPrompt) -> GenerationResult:
        # When a suitable model is available:
        #
        # if self._pipeline is None:
        #     from diffusers import DiffusionPipeline
        #     self._pipeline = DiffusionPipeline.from_pretrained(
        #         self.model_id, torch_dtype=torch.float16
        #     ).to("cuda")
        #
        # ... inference and export ...

        return GenerationResult(
            success=False,
            error=f"Local diffusion provider not yet implemented for {self.model_id}",
            provider=self.name,
        )

    def is_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def estimated_time(self, prompt: GenerationPrompt) -> float:
        return prompt.duration * 60


def create_provider(provider_name: str, videos_dir: str, **kwargs) -> GenerationProvider:
    """Factory function for creating providers from config."""
    providers = {
        "stub": StubProvider,
        "open_sora": OpenSoraProvider,
        "replicate": ReplicateProvider,
        "local_diffusion": LocalDiffusionProvider,
    }
    cls = providers.get(provider_name, StubProvider)
    return cls(videos_dir=videos_dir, **kwargs)
