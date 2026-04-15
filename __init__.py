"""
🔹 FrostzNeeko Nodes
Custom node pack for ComfyUI — nodes with a cyan neon theme.
"""

import os

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./js"

# ── Serve mascot image via ComfyUI API route ─────────────────────────
_MY_DIR = os.path.dirname(os.path.abspath(__file__))
_MASCOT_PATH = os.path.join(_MY_DIR, "img", "mascot.png")

try:
    from aiohttp import web
    import server

    @server.PromptServer.instance.routes.get("/FrostzNeeko/mascot")
    async def _serve_mascot(request):
        if os.path.isfile(_MASCOT_PATH):
            return web.FileResponse(_MASCOT_PATH)
        return web.Response(status=404, text="mascot not found")

    @server.PromptServer.instance.routes.get("/FrostzNeeko/metadata-image")
    async def _serve_metadata_image(request):
        path = request.query.get("path", "")
        if not path:
            return web.Response(status=400, text="path is required")
        if not os.path.isfile(path):
            return web.Response(status=404, text="image not found")
        ext = os.path.splitext(path)[1].lower()
        if ext not in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
            return web.Response(status=400, text="unsupported image type")
        return web.FileResponse(path)

except Exception:
    pass  # non-critical — mascot just won't show

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
