# 🚀 GitHub Push Guide

## Repository Structure

```
ARS/
├── README.md                 # Main documentation
├── LICENSE                   # Apache 2.0 License
├── .gitignore               # Git ignore rules
├── docker-compose.yml       # Docker orchestration
├── nginx.conf               # Nginx configuration
├── .env.example             # Example environment file (create .env with your token)
├── docs/                    # Detailed documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── PIPELINE.md          # Request pipeline
│   ├── ERRORS.md            # Error reference
│   ├── API.md               # API documentation (TODO)
│   ├── DEPLOYMENT.md        # Deployment guide (TODO)
│   └── TROUBLESHOOTING.md   # Troubleshooting (TODO)
├── backend/
│   └── Dockerfile           # vLLM container
├── proxy/
│   ├── Dockerfile           # Python proxy container
│   └── proxy.py             # Flask server (format conversion)
└── frontend/
    ├── index.html           # Main UI
    └── test.html            # Test page
```

---

## Pre-Push Checklist

### 1. Verify No Secrets

```bash
# Check for .env file (should be in .gitignore)
git status

# Should NOT see .env in staged files
# If you see it, remove:
git rm --cached .env
```

### 2. Create .env.example

```bash
# Create example file (safe to commit)
echo "HF_TOKEN=your_hugging_face_token_here" > .env.example

# Add to git
git add .env.example
```

### 3. Review Files

```bash
# See what will be committed
git status

# Review changes
git diff --cached
```

---

## Push to GitHub

### Initialize Repository (if not done)

```bash
cd /home/airoot/work_space/ARS

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Granite Speech Transcription System

- Live microphone transcription
- File upload support (MP3, WAV, WebM, OGG, FLAC, M4A)
- GPU-accelerated inference with vLLM
- Automatic audio format conversion
- Modern responsive UI
- Comprehensive documentation

Features:
- Real-time speech-to-text
- Multi-format audio support
- Volume boost for quiet audio
- Speech detection and validation
- Audio chunk accumulation
- CORS-enabled API

Tech Stack:
- Backend: vLLM, Python/Flask, ffmpeg
- Frontend: HTML5, CSS3, JavaScript
- Infrastructure: Docker, Docker Compose, Nginx
- GPU: NVIDIA CUDA

Documentation:
- README.md: Quick start and overview
- docs/ARCHITECTURE.md: System design
- docs/PIPELINE.md: Request flow
- docs/ERRORS.md: Error reference

License: Apache 2.0"
```

### Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `granite-speech-transcription` (or your choice)
3. Description: "Real-time speech-to-text transcription using IBM Granite 4.0 1B Speech model"
4. Visibility: Public (or Private)
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click "Create repository"

### Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/granite-speech-transcription.git

# Push to GitHub
git push -u origin main
```

### Verify Push

```bash
# Check remote
git remote -v

# Should show:
# origin  https://github.com/YOUR_USERNAME/granite-speech-transcription.git (fetch)
# origin  https://github.com/YOUR_USERNAME/granite-speech-transcription.git (push)
```

---

## Post-Push Actions

### 1. Update GitHub Repository Settings

- Add topics: `speech-to-text`, `granite`, `vllm`, `transcription`, `gpu`, `docker`
- Set default branch: `main`
- Enable Issues tab
- Enable Discussions tab (optional)

### 2. Add Repository Description

```
🎤 Real-time speech-to-text transcription powered by IBM Granite 4.0 1B Speech model

Features:
✅ Live microphone transcription
✅ File upload (MP3, WAV, WebM, OGG, FLAC, M4A)
✅ GPU-accelerated with vLLM
✅ Automatic format conversion
✅ Modern responsive UI

Quick Start:
docker compose up -d
# Open http://localhost:8080

Documentation: docs/
```

### 3. Create First Release (Optional)

1. Go to Releases → Create new release
2. Tag version: `v1.0.0`
3. Title: "Initial Release"
4. Description:
   ```
   ## 🎉 Initial Release

   ### Features
   - Live microphone transcription
   - File upload support
   - Multi-format audio conversion
   - GPU acceleration
   - Modern UI

   ### Installation
   ```bash
   git clone https://github.com/YOUR_USERNAME/granite-speech-transcription.git
   cd granite-speech-transcription
   echo "HF_TOKEN=your_token" > .env
   docker compose up -d
   ```

   ### Documentation
   See README.md and docs/ folder for complete documentation.
   ```

---

## Repository Badges

Add these to your README.md:

```markdown
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-green.svg)](https://www.docker.com/)
[![GPU](https://img.shields.io/badge/GPU-NVIDIA%20CUDA-blue.svg)](https://developer.nvidia.com/cuda-zone)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
```

---

## Security Reminders

### NEVER Commit:

- ❌ `.env` file (contains HF_TOKEN)
- ❌ API keys
- ❌ Passwords
- ❌ Personal credentials
- ❌ Private keys

### ALWAYS:

- ✅ Use `.env.example` with placeholder values
- ✅ Add sensitive files to `.gitignore`
- ✅ Review `git status` before committing
- ✅ Use GitHub Secrets for CI/CD

---

## Maintenance

### Update Documentation

```bash
# Edit documentation
nano docs/ARCHITECTURE.md

# Commit changes
git add docs/
git commit -m "docs: Update architecture diagram"
git push
```

### Add New Features

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ...

# Commit
git add .
git commit -m "feat: Add new feature"

# Push branch
git push -u origin feature/new-feature

# Create Pull Request on GitHub
```

---

## GitHub Pages (Optional)

To host documentation on GitHub Pages:

1. Go to Settings → Pages
2. Source: Deploy from branch
3. Branch: main, folder: /docs
4. Save
5. Access at: `https://YOUR_USERNAME.github.io/granite-speech-transcription/`

---

## Contributing

Create `CONTRIBUTING.md`:

```markdown
# Contributing to Granite Speech Transcription

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add comments for complex logic
- Include docstrings for functions

## Testing

- Test with live microphone
- Test with file uploads
- Test error handling
- Document any new dependencies

## Documentation

- Update README.md if adding features
- Add to docs/ folder for detailed docs
- Include examples for new features
```

---

## Support

### Issues

- Use GitHub Issues for bug reports
- Include:
  - System information (OS, GPU, Docker version)
  - Error messages (full logs)
  - Steps to reproduce
  - Expected vs actual behavior

### Discussions

- Use GitHub Discussions for:
  - Questions
  - Feature requests
  - Show and tell
  - General chat

---

## License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

**Model License:** IBM Granite 4.0 1B Speech is licensed under Apache 2.0 by IBM.

---

**Your repository is now ready for GitHub! 🎉**
