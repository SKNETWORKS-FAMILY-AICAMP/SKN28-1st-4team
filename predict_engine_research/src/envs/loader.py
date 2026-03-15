from pathlib import Path

from dotenv import load_dotenv


def load_project_env(project_root=None):
    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]
    else:
        project_root = Path(project_root).resolve()

    env_path = project_root / ".env"
    loaded = load_dotenv(env_path, override=False)
    return {
        "env_path": str(env_path),
        "exists": env_path.is_file(),
        "loaded": loaded,
    }
