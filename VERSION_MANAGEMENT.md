# Version Management

This project uses Git-based automatic versioning with semantic version tags.

## How It Works

- **Version Detection**: The application automatically detects its version from Git tags and commits
- **Dynamic Display**: The footer displays the current version fetched from `/api/v1/version`
- **Automatic Updates**: Version badges in README.md are automatically updated on each commit

## Version Formats

| Scenario | Version Display | Description |
|----------|----------------|-------------|
| **Release** | `v2.0.0` | Exact Git tag (production release) |
| **Development** | `v2.0.0-5-abc1234` | 5 commits after v2.0.0, at commit abc1234 |
| **Dirty Working Tree** | `v2.0.0-abc1234-dirty` | Uncommitted changes present |
| **No Tags** | `v1.0.0-abc1234` | Fallback version with commit hash |

## Release Workflow

### 1. Creating Releases

```bash
# Minor version (new features)
git tag v2.1.0 -m "Release v2.1.0: New feature description"
git push origin v2.1.0

# Major version (breaking changes)
git tag v3.0.0 -m "Release v3.0.0: Breaking changes description"
git push origin v3.0.0

# Patch version (bug fixes)
git tag v2.0.1 -m "Release v2.0.1: Bug fix description"
git push origin v2.0.1
```

### 2. Deployment

After creating a tag, deploy to production:

```bash
./manage.sh fast-deploy
```

The version will automatically update in:

- Footer version stamp
- API endpoint `/api/v1/version`
- README.md badge (on next commit)

### 3. Development Workflow

- **Main branch**: Shows development versions like `v2.0.0-5-abc1234`
- **Feature branches**: Show commits ahead of last release
- **Production**: Shows exact release tags like `v2.0.0`

## Setup

The Git hooks are automatically configured during installation. To manually install:

```bash
./setup-git-hooks.sh
```

## API Endpoint

The version API provides detailed information:

```bash
curl http://localhost:8000/api/v1/version
```

**Response:**

```json
{
  "version": "v2.0.0-5-abc1234",
  "timestamp": "2025-08-25T08:39:00.000000",
  "is_release": false,
  "base_version": "v2.0.0",
  "commits_ahead": 5,
  "commit_hash": "abc1234",
  "is_dirty": false,
  "app_name": "RMS Defragmenter"
}
```

## Benefits

- ✅ **No Manual Version Bumping**: Versions automatically follow Git workflow
- ✅ **Traceability**: Can always identify exact code running in production
- ✅ **Consistency**: Same version shown across UI, API, and documentation
- ✅ **Development Clarity**: Easy to see if running latest code or release
- ✅ **Semantic Versioning**: Follows industry standard practices

---

*This versioning system was implemented in v2.0.0 and replaces the previous hardcoded version numbers.*
