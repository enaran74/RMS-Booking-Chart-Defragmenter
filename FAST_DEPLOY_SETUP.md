# Fast Deploy Setup - Bind Mounts Configuration

## ✅ Working Configuration

The fast-deploy system is now properly configured to work with the existing Docker Hub image `enaran/rms-defragmenter:latest` using bind mounts.

### How It Works

1. **Base Image**: Uses the pre-built `enaran/rms-defragmenter:latest` from Docker Hub
2. **Bind Mounts**: Overlays your local code changes on top of the container
3. **Fast Deploy**: Changes are reflected immediately without rebuilding images

### Container Structure (from Dockerfile)

```
/app/
├── web/
│   ├── main.py              # FastAPI application entry point
│   └── app/                 # Web application code
│       ├── api/             # API endpoints
│       ├── services/        # Business logic (including RMS service)
│       ├── models/          # Database models
│       └── templates/       # HTML templates
├── original/                # CLI version files
├── defrag_analyzer.py       # Core algorithm (shared)
├── utils.py                 # Utilities (shared)
├── holiday_client.py        # Holiday integration (shared)
└── school_holiday_client.py # School holidays (shared)
```

### Bind Mount Configuration

```yaml
volumes:
  # Web application files
  - ./web_app/app:/app/web/app
  - ./web_app/main.py:/app/web/main.py
  # CLI shared files (accessible to both CLI and web app)
  - ./defrag_analyzer.py:/app/defrag_analyzer.py
  - ./utils.py:/app/utils.py
  - ./holiday_client.py:/app/holiday_client.py
  - ./school_holiday_client.py:/app/school_holiday_client.py
  - ./school_holidays.json:/app/school_holidays.json
  - ./rms_client.py:/app/rms_client.py
  - ./excel_generator.py:/app/excel_generator.py
  - ./email_sender.py:/app/email_sender.py
  # Original CLI files (for completeness)
  - ./start.py:/app/original/start.py
```

### Usage

1. **Make code changes** locally in:
   - `web_app/app/` - Web application changes
   - Root files - Shared CLI/web changes

2. **Deploy changes** instantly:
   ```bash
   ./manage.sh fast-deploy
   ```

3. **Container automatically** restarts and picks up your changes

### Benefits

- ✅ **No image rebuilds needed** for development
- ✅ **Instant deployment** of code changes
- ✅ **Works with existing Docker Hub images**
- ✅ **Preserves production image integrity**
- ✅ **Supports both web app and CLI changes**

### For Production Releases

When ready for a production release:
1. Push code to GitHub
2. Build new image via GitHub Actions → Docker Hub
3. Update docker-compose.yml image tag
4. Deploy new image

This gives you the best of both worlds: fast development iteration + stable production releases.
