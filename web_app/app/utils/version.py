"""
Git-based version detection utility.
Automatically generates semantic versions from Git tags and commits.
"""
import subprocess
import os
from pathlib import Path


def get_git_version() -> str:
    """
    Get version from Git tags and commits.
    
    Returns:
        - Exact tag: "v1.2.3"
        - Development: "v1.2.3-5-abc1234" (5 commits after v1.2.3)
        - Dirty working tree: "v1.2.3-5-abc1234-dirty"
        - Fallback: "v1.0.0-unknown"
    """
    # First, try to read from VERSION_INFO file (for containerized deployments)
    # Try multiple possible locations
    version_paths = [
        Path(__file__).parent.parent.parent / "VERSION_INFO",  # web_app/VERSION_INFO
        Path(__file__).parent.parent / "VERSION_INFO",         # app/VERSION_INFO
        Path("/app/web/VERSION_INFO"),                         # Docker container path (correct)
        Path("/app/app/VERSION_INFO"),                         # Docker container path (fallback)
    ]
    
    for version_file in version_paths:
        if version_file.exists():
            try:
                return version_file.read_text().strip()
            except Exception:
                continue
    
    try:
        # Get the project root (where .git is located)
        project_root = Path(__file__).parent.parent.parent.parent
        
        # Get full Git description with tags
        result = subprocess.run(
            ['git', 'describe', '--tags', '--dirty', '--always'],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            
            # If no tags exist, git describe returns just the commit hash
            if not version.startswith('v'):
                # Create a default version with commit hash
                return f"v1.0.0-{version}"
            
            return version
        else:
            # Fallback: try to get just the commit hash
            commit_result = subprocess.run(
                ['git', 'rev-parse', '--short', 'HEAD'],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if commit_result.returncode == 0:
                commit = commit_result.stdout.strip()
                return f"v1.0.0-{commit}"
            
            return "v1.0.0-unknown"
            
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        return "v1.0.0-unknown"


def get_version_info() -> dict:
    """
    Get detailed version information.
    
    Returns:
        dict: {
            'version': 'v1.2.3-5-abc1234',
            'is_release': False,
            'base_version': 'v1.2.3',
            'commits_ahead': 5,
            'commit_hash': 'abc1234',
            'is_dirty': False
        }
    """
    version = get_git_version()
    
    # Parse the version string
    is_dirty = version.endswith('-dirty')
    if is_dirty:
        version = version[:-6]  # Remove '-dirty'
    
    parts = version.split('-')
    
    if len(parts) == 1:
        # Exact tag release
        return {
            'version': version,
            'is_release': True,
            'base_version': version,
            'commits_ahead': 0,
            'commit_hash': None,
            'is_dirty': is_dirty
        }
    elif len(parts) >= 3:
        # Development version: v1.2.3-5-abc1234
        base_version = parts[0]
        commits_ahead = int(parts[1]) if parts[1].isdigit() else 0
        commit_hash = parts[2] if len(parts) > 2 else None
        
        return {
            'version': get_git_version(),
            'is_release': False,
            'base_version': base_version,
            'commits_ahead': commits_ahead,
            'commit_hash': commit_hash,
            'is_dirty': is_dirty
        }
    else:
        # Fallback version
        return {
            'version': version,
            'is_release': False,
            'base_version': 'v1.0.0',
            'commits_ahead': 0,
            'commit_hash': parts[1] if len(parts) > 1 else None,
            'is_dirty': is_dirty
        }


if __name__ == "__main__":
    # Test the version detection
    print(f"Version: {get_git_version()}")
    print(f"Version info: {get_version_info()}")
