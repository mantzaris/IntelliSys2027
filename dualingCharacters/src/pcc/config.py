"""Typed, serializable budgets; one configuration governs every comparator."""
from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass(frozen=True)
class RunConfig:
    model: str = "qwen"
    condition: str = "C5"
    seed: int = 17
    precision: str = "bf16"
    engine: str = "transformers"
    structured_decoding: bool = False
    batch_size: int = 8
    max_input_tokens: int = 4096
    answer_tokens: int = 256
    character_tokens: int = 128
    retrieval_messages: int = 8
    recent_messages: int = 4
    history_actions: int = 6
    intervention_opportunities: int = 12
    lora_rank: int = 8
    lora_alpha: int = 16
    learning_rate: float = 0.0001
    max_grad_norm: float = 1.0
    train_steps: int = 64
    train_tokens_per_step: int = 4096
    refresh_rounds: int = 2
    active_gpu_hours_ceiling: float = 96.0
    max_run_seconds: int = 7200
    phase: str = "pilot"

    def __post_init__(self):
        if self.precision not in {"bf16", "nf4"}:
            raise ValueError("precision must be bf16 or nf4")
        if self.engine not in {"transformers","vllm"}:
            raise ValueError("unknown inference engine")
        if self.condition not in {"base", "C1", "C2", "C3", "C4", "C5", "C6", "A1", "A2", "A3"}:
            raise ValueError("unknown condition")
        if not (0 < self.active_gpu_hours_ceiling <= 96):
            raise ValueError("GPU ceiling cannot exceed author authorization")
        if self.refresh_rounds < 1 or self.train_steps < 1:
            raise ValueError("positive training rounds and steps required")

    def save(self, path: Path):
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")

    @classmethod
    def load(cls, path: Path):
        return cls(**json.loads(path.read_text()))
