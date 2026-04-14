import { app } from "../../scripts/app.js";

/*
 * FrostzNeeko — KSampler Preview: Section Headers + Styled Toggles
 * Cyan neon theme
 */

const CYAN = {
    accent:     "#00E5FF",
    glow:       "#00BCD4",
    titleBar:   "#00363A",
    body:       "#0C1B1E",
    dim:        "rgba(0, 229, 255, 0.35)",
    text:       "#E0F7FA",
    off:        "#0a1518",
    offBorder:  "rgba(255,255,255,0.12)",
    onColor:    "#00E5FF",
    red:        "#00BCD4",
};

const SECTIONS = [
    { label: "Sampling",    before: "seed" },
    { label: "Latent Size", before: "width" },
    { label: "Preview",     before: "preview_method" },
    { label: "Upscaler",    before: "upscale_model_name" },
    { label: "Detailers",   before: "detailer_1_name" },
];

function createSectionHeader(label) {
    return {
        name: `fn_sec_${label.replace(/\s/g, "_").toLowerCase()}`,
        type: "custom",
        value: null,
        options: { serialize: false },
        computeSize: () => [200, 24],
        draw: function (ctx, node) {
            const fullW = node.size[0];
            const y = this.last_y ?? 0;
            const lineY = y + 18;

            ctx.save();

            // Label text
            ctx.font = "bold 12px Inter, Segoe UI, Arial, sans-serif";
            ctx.fillStyle = CYAN.text;
            ctx.textBaseline = "middle";
            ctx.textAlign = "left";
            ctx.fillText(label, 12, lineY);

            // Measure text to start line after it
            const textW = ctx.measureText(label).width;

            // Horizontal line from end of text to right edge
            ctx.strokeStyle = CYAN.dim;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(12 + textW + 8, lineY);
            ctx.lineTo(fullW - 8, lineY);
            ctx.stroke();

            ctx.restore();
        },
    };
}

app.registerExtension({
    name: "FrostzNeeko.KSamplerSections",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNKSamplerPreview") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            if (!this.widgets) return;

            // Insert section headers (reverse to keep indices stable)
            for (let s = SECTIONS.length - 1; s >= 0; s--) {
                const sec = SECTIONS[s];
                const idx = this.widgets.findIndex((w) => w.name === sec.before);
                if (idx >= 0) {
                    this.widgets.splice(idx, 0, createSectionHeader(sec.label));
                }
            }

            // Recalc size
            const self = this;
            requestAnimationFrame(() => {
                const sz = self.computeSize();
                sz[0] = Math.max(sz[0], 400);
                self.setSize(sz);
                self.setDirtyCanvas(true, true);
            });
        };

        // ── Draw custom toggle overlays on detailer_enabled widgets ─
        const origFg = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origFg?.apply(this, arguments);
            if (this.flags?.collapsed || !this.widgets) return;

            for (const w of this.widgets) {
                if (!w.name || !w.name.includes("_enabled")) continue;
                if (w.last_y === undefined) continue;

                const fullW = this.size[0];
                const y = w.last_y;
                const h = LiteGraph.NODE_WIDGET_HEIGHT || 20;
                const isOn = !!w.value;

                ctx.save();

                // ── Pill toggle on right side ───────────────
                const pillW = 38;
                const pillH = 16;
                const pillX = fullW - pillW - 16;
                const pillY = y + (h - pillH) / 2;
                const pillR = pillH / 2;

                // Track
                ctx.fillStyle = isOn ? "rgba(0, 229, 255, 0.3)" : CYAN.off;
                ctx.beginPath();
                ctx.roundRect(pillX, pillY, pillW, pillH, pillR);
                ctx.fill();

                ctx.strokeStyle = isOn ? CYAN.onColor : CYAN.offBorder;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(pillX, pillY, pillW, pillH, pillR);
                ctx.stroke();

                // Knob
                const knobR = 5;
                const knobX = isOn ? pillX + pillW - knobR - 3 : pillX + knobR + 3;
                const knobY = pillY + pillH / 2;

                if (isOn) {
                    ctx.shadowColor = CYAN.onColor;
                    ctx.shadowBlur = 6;
                }
                ctx.fillStyle = isOn ? CYAN.onColor : "#555";
                ctx.beginPath();
                ctx.arc(knobX, knobY, knobR, 0, Math.PI * 2);
                ctx.fill();

                ctx.restore();
            }
        };
    },
});
