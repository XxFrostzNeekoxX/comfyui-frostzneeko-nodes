import { app } from "../../scripts/app.js";

/*
 * FrostzNeeko Nodes — Cyan Neon Theme v2
 * Clean neon glow, bold titles, premium look.
 */

const FROTSZ_NODES = [
    "FNPromptFromFile",
    "FNClipDualEncode",
    "FNClipAdvanced",
    "FNCheckpointLoader",
    "FNKSamplerPreview",
    "FNFaceDetailer",
    "FNImageSaver",
];

const CYAN = {
    titleBar:   "#00363A",
    body:       "#0C1B1E",
    borderOuter:"rgba(0, 229, 255, 0.08)",
    borderInner:"rgba(0, 229, 255, 0.35)",
    glow:       "#00BCD4",
    titleText:  "#E0F7FA",
};

app.registerExtension({
    name: "FrostzNeeko.CyanNeonTheme",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (!FROTSZ_NODES.includes(nodeData.name)) return;

        // ── colours ─────────────────────────────────────────────
        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            this.color  = CYAN.titleBar;
            this.bgcolor = CYAN.body;
        };

        // ── fill body fully + neon glow border ──────────────────
        const origBg = nodeType.prototype.onDrawBackground;
        nodeType.prototype.onDrawBackground = function (ctx) {
            origBg?.apply(this, arguments);
            if (this.flags?.collapsed) return;

            const titleH = LiteGraph.NODE_TITLE_HEIGHT || 20;
            const w = this.size[0];
            const h = this.size[1];
            const r = 6;

            ctx.save();

            // ── Fill the entire body area (including corners) ───
            ctx.fillStyle = CYAN.body;
            ctx.beginPath();
            ctx.roundRect(0, 0, w, h, [0, 0, r, r]);
            ctx.fill();

            // ── Fill the title area corners too ─────────────────
            ctx.fillStyle = CYAN.titleBar;
            ctx.beginPath();
            ctx.roundRect(0, -titleH, w, titleH, [r, r, 0, 0]);
            ctx.fill();

            // soft outer glow
            const totalH = h + titleH;
            ctx.shadowColor = CYAN.glow;
            ctx.shadowBlur  = 14;
            ctx.strokeStyle = CYAN.borderOuter;
            ctx.lineWidth   = 3;
            ctx.beginPath();
            ctx.roundRect(0, -titleH, w, totalH, r);
            ctx.stroke();

            // crisp inner border
            ctx.shadowBlur  = 6;
            ctx.strokeStyle = CYAN.borderInner;
            ctx.lineWidth   = 1;
            ctx.beginPath();
            ctx.roundRect(0, -titleH, w, totalH, r);
            ctx.stroke();

            ctx.restore();
        };

        // ── bold white title ────────────────────────────────────
        const origFg = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origFg?.apply(this, arguments);
            if (this.flags?.collapsed) return;

            const titleH = LiteGraph.NODE_TITLE_HEIGHT || 20;

            ctx.save();
            // cover default title text
            ctx.fillStyle = CYAN.titleBar;
            ctx.fillRect(10, -titleH + 1, this.size[0] - 20, titleH - 2);

            // bold title
            ctx.font = "bold 13px Inter, Segoe UI, Arial, sans-serif";
            ctx.fillStyle = CYAN.titleText;
            ctx.textBaseline = "middle";
            ctx.textAlign = "left";
            ctx.shadowColor = CYAN.glow;
            ctx.shadowBlur = 4;
            ctx.fillText(this.getTitle(), 14, -titleH / 2 + 1);
            ctx.restore();
        };
    },

    async nodeCreated(node) {
        if (!FROTSZ_NODES.includes(node.type)) return;
        node.color  = CYAN.titleBar;
        node.bgcolor = CYAN.body;
    },
});
