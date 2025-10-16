# Text2Video Backend

A lightweight FastAPI backend for text-to-video and text-to-image generation with local LLM integration and web automation capabilities.

## Features

- 🚀 **FastAPI Backend** - High-performance async API
- 🤖 **Local LLM Integration** - Ollama support for prompt enhancement
- 🎨 **Multiple Generators** - ComfyUI, Web automation, External APIs
- 📊 **Usage Analytics** - Built-in SQLite tracking
- 🌐 **Web Automation** - Playwright for web-based generators
- 🔧 **Easy Setup** - Docker support and simple configuration

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/silva2kand/text2video-backend.git
cd text2video-backend

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Copy environment file
cp .env.example .env
# Edit .env with your configurations
```

### 2. Configure Services

**Local Ollama (Recommended):**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.2
```

**ComfyUI (Optional):**
```bash
# Install ComfyUI in a separate directory
git clone https://github.com/comfyanonymous/ComfyUI.git
cd ComfyUI && pip install -r requirements.txt
python main.py
```

### 3. Run the Backend

```bash
# Development
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn main:app --host 0.0.0.0 --port 8000
```

## API Endpoints

### Core Endpoints

- `GET /` - API status
- `GET /health` - Health check
- `GET /stats` - Usage statistics

### Generation Endpoints

- `POST /enhance-prompt` - Enhance text prompts using local LLM
- `POST /generate-image` - Generate images
- `POST /generate-video` - Generate videos

### Example Requests

**Enhance Prompt:**
```json
POST /enhance-prompt
{
  "text": "a cat in space",
  "enhance": true
}
```

**Generate Image:**
```json
POST /generate-image
{
  "text": "a beautiful sunset over mountains",
  "enhance": true,
  "generator": "comfyui"
}
```

**Generate Video:**
```json
POST /generate-video
{
  "prompt": "waves crashing on a beach",
  "duration": 5,
  "enhance": true
}
```

## Configuration

### Environment Variables

```env
# Local Services
OLLAMA_URL=http://localhost:11434
COMFY_URL=http://localhost:8188

# External APIs (optional)
HUGGINGFACE_TOKEN=your_token
REPLICATE_TOKEN=your_token
OPENAI_API_KEY=your_key

# Settings
BROWSER_HEADLESS=true
WEB_TIMEOUT=30
DEBUG=false
```

### Supported Generators

1. **ComfyUI** (Local) - Preferred for best quality
2. **Web Automation** - Fallback using Playwright
3. **External APIs** - Hugging Face, Replicate, etc.

## Architecture

```
text2video-backend/
├── main.py              # FastAPI app and routes
├── counters.py          # Usage analytics
├── playwright_runner.py # Web automation
├── requirements.txt     # Dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Usage Analytics

The backend automatically tracks:
- Total API requests
- Image/video generations
- Prompt enhancements
- Daily/weekly statistics
- Endpoint usage patterns

Access stats at: `GET /stats`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API examples

---

**Ready to generate!** 🎬✨