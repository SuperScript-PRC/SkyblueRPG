import shutil
from pathlib import Path

WORKSPACE_PLUGIN_DIR = Path(
    "D:/", "Super", "gitclone", "ToolDelta", "插件文件", "ToolDelta类式插件"
)

repo_plugin_dir = Path(__file__).parent.parent.parent / "ToolDelta类式插件"
for plugin_path in repo_plugin_dir.iterdir():
    if plugin_path.is_dir():
        target_path = WORKSPACE_PLUGIN_DIR / plugin_path.name
        shutil.copytree(target_path, plugin_path, dirs_exist_ok=True)
