import asyncio
import tempfile
import os
import base64
from typing import Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, Page

async def run_web_generator(prompt: str, site_url: str = "https://lmarena.ai", timeout: int = 30) -> Dict[str, Any]:
    """
    Generate content using web-based AI generators via browser automation
    
    Args:
        prompt: Text prompt for generation
        site_url: URL of the generator site
        timeout: Timeout in seconds
    
    Returns:
        Dictionary with generation results
    """
    result = {
        "status": "failed",
        "prompt": prompt,
        "site": site_url,
        "output": None,
        "error": None
    }
    
    try:
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            
            try:
                page = await browser.new_page()
                
                # Set viewport and user agent
                await page.set_viewport_size({"width": 1280, "height": 720})
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                
                # Navigate to the site
                await page.goto(site_url, timeout=timeout*1000)
                await page.wait_for_load_state('networkidle', timeout=timeout*1000)
                
                # Site-specific automation
                if "lmarena.ai" in site_url:
                    result = await handle_lmarena(page, prompt, timeout)
                elif "huggingface.co" in site_url:
                    result = await handle_huggingface(page, prompt, timeout)
                elif "replicate.com" in site_url:
                    result = await handle_replicate(page, prompt, timeout)
                else:
                    # Generic approach - look for common input patterns
                    result = await handle_generic_site(page, prompt, timeout)
                
            finally:
                await browser.close()
                
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "error"
    
    return result

async def handle_lmarena(page: Page, prompt: str, timeout: int) -> Dict[str, Any]:
    """Handle lmarena.ai specific automation"""
    try:
        # Wait for and find text input
        await page.wait_for_selector('textarea, input[type="text"]', timeout=timeout*1000)
        
        # Find the main prompt input
        input_selector = 'textarea'
        await page.fill(input_selector, prompt)
        
        # Look for generate/submit button
        button_selectors = [
            'button:has-text("Generate")',
            'button:has-text("Submit")', 
            'button:has-text("Create")',
            'button[type="submit"]'
        ]
        
        button_clicked = False
        for selector in button_selectors:
            try:
                await page.click(selector, timeout=5000)
                button_clicked = True
                break
            except:
                continue
        
        if not button_clicked:
            return {"status": "failed", "error": "Could not find generate button"}
        
        # Wait for results
        await page.wait_for_timeout(3000)  # Initial wait
        
        # Look for generated content
        await page.wait_for_selector('img, video, .result, .output', timeout=timeout*1000)
        
        # Capture results
        images = await page.query_selector_all('img')
        videos = await page.query_selector_all('video')
        
        output = []
        
        # Process images
        for img in images[-3:]:  # Get last 3 images (likely results)
            src = await img.get_attribute('src')
            if src and ('blob:' in src or 'data:' in src or 'generated' in src):
                output.append({"type": "image", "url": src})
        
        # Process videos
        for video in videos[-2:]:  # Get last 2 videos
            src = await video.get_attribute('src')
            if src:
                output.append({"type": "video", "url": src})
        
        return {
            "status": "success" if output else "no_output",
            "prompt": prompt,
            "site": "lmarena.ai",
            "output": output
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def handle_huggingface(page: Page, prompt: str, timeout: int) -> Dict[str, Any]:
    """Handle Hugging Face Spaces automation"""
    try:
        # Wait for Gradio interface
        await page.wait_for_selector('.gradio-container', timeout=timeout*1000)
        
        # Find text input in Gradio
        await page.fill('textarea, input[type="text"]', prompt)
        
        # Click submit
        await page.click('button:has-text("Submit"), button:has-text("Generate")')
        
        # Wait for output
        await page.wait_for_selector('.output, .gallery, img', timeout=timeout*1000)
        
        # Capture generated content
        content = await page.query_selector_all('img, video')
        output = []
        
        for item in content[-2:]:
            src = await item.get_attribute('src')
            tag_name = await item.evaluate('el => el.tagName.toLowerCase()')
            if src:
                output.append({"type": tag_name, "url": src})
        
        return {
            "status": "success" if output else "no_output",
            "prompt": prompt,
            "site": "huggingface.co",
            "output": output
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def handle_replicate(page: Page, prompt: str, timeout: int) -> Dict[str, Any]:
    """Handle Replicate.com automation"""
    try:
        # Wait for input form
        await page.wait_for_selector('input, textarea', timeout=timeout*1000)
        
        # Fill prompt
        await page.fill('textarea, input[type="text"]', prompt)
        
        # Submit
        await page.click('button:has-text("Run"), button[type="submit"]')
        
        # Wait for results
        await page.wait_for_selector('.output, img, video', timeout=timeout*1000)
        
        # Get results
        results = await page.query_selector_all('img, video')
        output = []
        
        for result in results:
            src = await result.get_attribute('src')
            tag_name = await result.evaluate('el => el.tagName.toLowerCase()')
            if src and 'replicate' in src:
                output.append({"type": tag_name, "url": src})
        
        return {
            "status": "success" if output else "no_output",
            "prompt": prompt,
            "site": "replicate.com",
            "output": output
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

async def handle_generic_site(page: Page, prompt: str, timeout: int) -> Dict[str, Any]:
    """Generic handler for unknown sites"""
    try:
        # Try to find text input
        input_found = False
        input_selectors = ['textarea', 'input[type="text"]', '[contenteditable="true"]']
        
        for selector in input_selectors:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                await page.fill(selector, prompt)
                input_found = True
                break
            except:
                continue
        
        if not input_found:
            return {"status": "failed", "error": "No input field found"}
        
        # Try to find and click submit button
        button_selectors = [
            'button:has-text("Generate")',
            'button:has-text("Submit")',
            'button:has-text("Create")',
            'button:has-text("Run")',
            'button[type="submit"]',
            '.btn:has-text("Generate")'
        ]
        
        button_clicked = False
        for selector in button_selectors:
            try:
                await page.click(selector, timeout=3000)
                button_clicked = True
                break
            except:
                continue
        
        if not button_clicked:
            return {"status": "failed", "error": "No submit button found"}
        
        # Wait for potential results
        await page.wait_for_timeout(5000)
        
        # Look for generated content
        content = await page.query_selector_all('img, video')
        output = []
        
        for item in content:
            src = await item.get_attribute('src')
            tag_name = await item.evaluate('el => el.tagName.toLowerCase()')
            if src and not src.startswith('data:image/svg'):
                output.append({"type": tag_name, "url": src})
        
        return {
            "status": "success" if output else "no_output",
            "prompt": prompt,
            "site": "generic",
            "output": output[-3:] if output else []  # Last 3 items
        }
        
    except Exception as e:
        return {"status": "failed", "error": str(e)}

# Utility function for downloading generated content
async def download_content(url: str, output_dir: str = "./outputs") -> Optional[str]:
    """Download generated content from URL"""
    try:
        import aiohttp
        import aiofiles
        
        os.makedirs(output_dir, exist_ok=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    # Determine file extension
                    content_type = response.headers.get('content-type', '')
                    if 'image' in content_type:
                        ext = '.png' if 'png' in content_type else '.jpg'
                    elif 'video' in content_type:
                        ext = '.mp4'
                    else:
                        ext = '.bin'
                    
                    # Generate filename
                    filename = f"generated_{int(asyncio.get_event_loop().time())}{ext}"
                    filepath = os.path.join(output_dir, filename)
                    
                    # Save file
                    async with aiofiles.open(filepath, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                    
                    return filepath
                    
    except Exception as e:
        print(f"Download failed: {e}")
        return None