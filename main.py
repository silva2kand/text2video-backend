import os
import asyncio
import json
import datetime
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from counters import ApiCounters
from playwright_runner import run_web_generator

app = FastAPI(title="Text2Video Backend", version="1.0.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
counters = ApiCounters()

# Request models
class TextPrompt(BaseModel):
    text: str
    enhance: bool = True
    generator: str = "comfyui"  # comfyui, replicate, huggingface

class VideoRequest(BaseModel):
    prompt: str
    duration: int = 5
    enhance: bool = True

@app.get("/")
async def root():
    return {"message": "Text2Video Backend API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.datetime.now().isoformat()}

@app.get("/stats")
async def get_stats():
    return counters.get_stats()

@app.post("/enhance-prompt")
async def enhance_prompt(request: TextPrompt):
    """Enhance text prompt using local LLM"""
    try:
        counters.increment("prompt_enhancements")
        
        if not request.enhance:
            return {"original": request.text, "enhanced": request.text}
        
        # Try Ollama first
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{ollama_url}/api/generate",
                    json={
                        "model": "llama3.2",
                        "prompt": f"Enhance this prompt for AI image/video generation. Make it more detailed and descriptive while keeping the core concept. Original: {request.text}",
                        "stream": False
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    enhanced = response.json().get("response", request.text)
                    return {"original": request.text, "enhanced": enhanced.strip()}
            except:
                pass
        
        # Fallback: return original if enhancement fails
        return {"original": request.text, "enhanced": request.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-image")
async def generate_image(request: TextPrompt, background_tasks: BackgroundTasks):
    """Generate image using specified backend"""
    try:
        counters.increment("image_generations")
        
        # Enhance prompt if requested
        prompt = request.text
        if request.enhance:
            enhance_result = await enhance_prompt(request)
            prompt = enhance_result["enhanced"]
        
        if request.generator == "comfyui":
            return await generate_with_comfyui(prompt, "image")
        elif request.generator == "web":
            return await run_web_generator(prompt)
        else:
            raise HTTPException(status_code=400, detail="Unsupported generator")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-video")
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Generate video using ComfyUI or fallback"""
    try:
        counters.increment("video_generations")
        
        # Enhance prompt if requested
        prompt = request.prompt
        if request.enhance:
            enhance_result = await enhance_prompt(TextPrompt(text=request.prompt, enhance=True))
            prompt = enhance_result["enhanced"]
        
        return await generate_with_comfyui(prompt, "video", request.duration)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def generate_with_comfyui(prompt: str, type: str = "image", duration: int = 5):
    """Generate content using ComfyUI"""
    comfy_url = os.getenv("COMFY_URL", "http://localhost:8188")
    
    # Basic workflow for ComfyUI (you'll need to customize this)
    workflow = {
        "prompt": prompt,
        "type": type,
        "duration": duration if type == "video" else None
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Check if ComfyUI is running
            health_response = await client.get(f"{comfy_url}/system_stats", timeout=5.0)
            if health_response.status_code != 200:
                raise HTTPException(status_code=503, detail="ComfyUI not available")
            
            # Submit generation job (customize endpoint as needed)
            response = await client.post(
                f"{comfy_url}/prompt",
                json={"prompt": workflow},
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "generated",
                    "type": type,
                    "prompt": prompt,
                    "result": result,
                    "timestamp": datetime.datetime.now().isoformat()
                }
            else:
                raise HTTPException(status_code=500, detail="ComfyUI generation failed")
                
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Generation timeout")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ComfyUI error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)