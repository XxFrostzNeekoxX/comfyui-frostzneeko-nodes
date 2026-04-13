import { app } from "../../scripts/app.js";

/*
 * FrotszNeeko — Prompt From File: mascot image + display updater
 *
 * Strategy: spacer widget reserves space, onDrawForeground renders
 * the image at the spacer's actual Y position (via widget.last_y).
 */

// ── Mascot image loader ─────────────────────────────────────────────
let mascotImg = null;
let mascotLoaded = false;

function ensureMascotLoaded() {
    if (mascotImg) return;
    mascotImg = new Image();
    mascotImg.crossOrigin = "anonymous";
    mascotImg.onload = () => {
        mascotLoaded = true;
        app.graph?.setDirtyCanvas(true, true);
    };
    mascotImg.onerror = () => {
        console.warn("[FrotszNeeko] Could not load mascot");
        mascotImg = null;
    };
    mascotImg.src = "/frotszneeko/mascot?v=" + Date.now();
}
ensureMascotLoaded();

const IMG_BLOCK_H = 160;

app.registerExtension({
    name: "FrotszNeeko.PromptFromFileDisplay",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNPromptFromFile") return;

        // ── onExecuted: update display widgets ──────────────────────
        const origExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (data) {
            origExecuted?.apply(this, arguments);
            if (!data) return;

            if (data.current_prompt?.length > 0) {
                const w = this.widgets?.find((w) => w.name === "current_prompt");
                if (w) w.value = data.current_prompt[0] || "";
            }
            if (data.active_loras_wildcards?.length > 0) {
                const w = this.widgets?.find((w) => w.name === "active_loras_wildcards");
                if (w) w.value = data.active_loras_wildcards[0] || "";
            }
            this.setDirtyCanvas(true, true);
        };

        // ── onNodeCreated: add spacer widget ────────────────────────
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            // Silent spacer — only reserves vertical space
            const spacer = {
                name: "fn_mascot_spacer",
                type: "custom",
                value: null,
                options: { serialize: false },
                computeSize: () => [200, IMG_BLOCK_H],
                draw: () => {}, // empty — rendering done in onDrawForeground
            };

            if (this.widgets) {
                this.widgets.unshift(spacer);
            }

            const self = this;
            requestAnimationFrame(() => {
                // Set a wider default node size
                const computed = self.computeSize();
                computed[0] = Math.max(computed[0], 400);
                self.setSize(computed);
                self.setDirtyCanvas(true, true);
            });
        };

        // ── onDrawForeground: render mascot at spacer position ──────
        const origFg = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origFg?.apply(this, arguments);
            if (this.flags?.collapsed) return;
            if (!mascotImg || !mascotLoaded) return;

            // Find the spacer widget to get its actual Y position
            const spacer = this.widgets?.find((w) => w.name === "fn_mascot_spacer");
            if (!spacer) return;

            const y = spacer.last_y ?? 0;
            const nodeW = this.size[0];

            // Fill the full spacer area — stretch up into slot area
            const imgW = nodeW - 12;
            const imgH = IMG_BLOCK_H + 130;
            const imgX = 6;
            const imgY = y - 130;

            ctx.save();
            ctx.drawImage(mascotImg, imgX, imgY, imgW, imgH);
            ctx.restore();
        };
    },
});
