import { app } from "../../scripts/app.js";

/*
 * FrostzNeeko — Metadata Reader UI polish
 * Gives FNMetadataReader the same visual/UX feel as other FN nodes.
 */

const CYAN = {
    dim: "rgba(0, 229, 255, 0.35)",
    text: "#E0F7FA",
};

function createSectionHeader(label) {
    return {
        name: `fn_meta_sec_${label.replace(/\s/g, "_").toLowerCase()}`,
        type: "custom",
        value: null,
        options: { serialize: false },
        computeSize: () => [220, 24],
        draw: function (ctx, node) {
            const fullW = node.size[0];
            const y = this.last_y ?? 0;
            const lineY = y + 18;

            ctx.save();
            ctx.font = "bold 12px Inter, Segoe UI, Arial, sans-serif";
            ctx.fillStyle = CYAN.text;
            ctx.textBaseline = "middle";
            ctx.textAlign = "left";
            ctx.fillText(label, 12, lineY);

            const textW = ctx.measureText(label).width;
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
    name: "FrostzNeeko.MetadataReaderUI",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNMetadataReader") return;

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            if (!this.widgets) return;

            const idxPath = this.widgets.findIndex((w) => w.name === "image_path");
            if (idxPath >= 0) this.widgets.splice(idxPath, 0, createSectionHeader("Image Source"));

            const idxToggle = this.widgets.findIndex((w) => w.name === "prefer_output_dir");
            if (idxToggle >= 0) this.widgets.splice(idxToggle, 0, createSectionHeader("Resolve Mode"));

            const idxSel = this.widgets.findIndex((w) => w.name === "selection_mode");
            if (idxSel >= 0) this.widgets.splice(idxSel, 0, createSectionHeader("Folder Navigation"));

            const imageIndexWidget = this.widgets.find((w) => w.name === "image_index");
            const selectionModeWidget = this.widgets.find((w) => w.name === "selection_mode");

            this._fnMetaPath = "";
            this._fnMetaText = "";
            this._fnMetaImage = null;
            this._fnMetaImageReady = false;
            this._fnMetaImageSrc = "";

            const imageBox = {
                name: "fn_meta_image_box",
                type: "custom",
                value: null,
                options: { serialize: false },
                computeSize: () => [380, 300],
                draw: function (ctx, node, width, y, h) {
                    const x = 8;
                    const w = node.size[0] - 16;
                    const boxH = h - 8;
                    ctx.save();
                    ctx.fillStyle = "rgba(0,0,0,0.35)";
                    ctx.strokeStyle = "rgba(0,229,255,0.25)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(x, y + 4, w, boxH, 6);
                    ctx.fill();
                    ctx.stroke();

                    if (node._fnMetaImageReady && node._fnMetaImage) {
                        const img = node._fnMetaImage;
                        const ratio = Math.min((w - 8) / img.width, (boxH - 30) / img.height);
                        const iw = Math.max(1, Math.floor(img.width * ratio));
                        const ih = Math.max(1, Math.floor(img.height * ratio));
                        const ix = x + Math.floor((w - iw) / 2);
                        const iy = y + 10 + Math.floor((boxH - ih) / 2);
                        ctx.drawImage(img, ix, iy, iw, ih);
                        ctx.fillStyle = CYAN.text;
                        ctx.font = "11px Inter, Segoe UI, Arial, sans-serif";
                        ctx.textAlign = "center";
                        ctx.fillText(`${img.width} x ${img.height}`, x + w / 2, y + boxH - 8);
                    } else {
                        ctx.fillStyle = CYAN.text;
                        ctx.font = "12px Inter, Segoe UI, Arial, sans-serif";
                        ctx.textAlign = "center";
                        ctx.fillText("Run node to load image preview", x + w / 2, y + boxH / 2);
                    }
                    ctx.restore();
                },
            };
            this.widgets.push(imageBox);

            const metadataBox = {
                name: "fn_meta_text_box",
                type: "custom",
                value: null,
                options: { serialize: false },
                computeSize: () => [380, 230],
                draw: function (ctx, node, width, y, h) {
                    const x = 8;
                    const w = node.size[0] - 16;
                    const boxH = h - 8;
                    const text = node._fnMetaText || "Metadata will appear here after run.";
                    const lines = text.split("\n");

                    ctx.save();
                    ctx.fillStyle = "rgba(0,0,0,0.32)";
                    ctx.strokeStyle = "rgba(0,229,255,0.25)";
                    ctx.lineWidth = 1;
                    ctx.beginPath();
                    ctx.roundRect(x, y + 4, w, boxH, 6);
                    ctx.fill();
                    ctx.stroke();

                    ctx.fillStyle = CYAN.text;
                    ctx.font = "11px Consolas, Menlo, monospace";
                    ctx.textAlign = "left";
                    ctx.textBaseline = "top";

                    const maxLines = Math.max(1, Math.floor((boxH - 14) / 14));
                    for (let i = 0; i < Math.min(lines.length, maxLines); i++) {
                        let line = lines[i];
                        if (line.length > 110) line = line.slice(0, 107) + "...";
                        ctx.fillText(line, x + 8, y + 10 + i * 14);
                    }
                    ctx.restore();
                },
            };
            this.widgets.push(metadataBox);

            const prevBtn = this.addWidget("button", "⬅ Prev Image", null, () => {
                if (selectionModeWidget) selectionModeWidget.value = "index";
                if (imageIndexWidget) imageIndexWidget.value = Math.max(0, (imageIndexWidget.value || 0) - 1);
                this.setDirtyCanvas(true, true);
            });
            const nextBtn = this.addWidget("button", "Next Image ➡", null, () => {
                if (selectionModeWidget) selectionModeWidget.value = "index";
                if (imageIndexWidget) imageIndexWidget.value = (imageIndexWidget.value || 0) + 1;
                this.setDirtyCanvas(true, true);
            });
            prevBtn.options = { serialize: false };
            nextBtn.options = { serialize: false };

            const self = this;
            requestAnimationFrame(() => {
                const sz = self.computeSize();
                sz[0] = Math.max(sz[0], 420);
                sz[1] = Math.max(sz[1], 860);
                self.setSize(sz);
                self.setDirtyCanvas(true, true);
            });
        };

        const origExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (data) {
            origExecuted?.apply(this, arguments);
            if (!data) return;

            if (Array.isArray(data.selected_image_path) && data.selected_image_path.length > 0) {
                this._fnMetaPath = data.selected_image_path[0] || "";
            }
            if (Array.isArray(data.pretty_metadata) && data.pretty_metadata.length > 0) {
                this._fnMetaText = data.pretty_metadata[0] || "";
            }

            if (this._fnMetaPath) {
                const src = `/FrostzNeeko/metadata-image?path=${encodeURIComponent(this._fnMetaPath)}&v=${Date.now()}`;
                if (src !== this._fnMetaImageSrc) {
                    const img = new Image();
                    img.onload = () => {
                        this._fnMetaImage = img;
                        this._fnMetaImageReady = true;
                        this.setDirtyCanvas(true, true);
                    };
                    img.onerror = () => {
                        this._fnMetaImage = null;
                        this._fnMetaImageReady = false;
                        this.setDirtyCanvas(true, true);
                    };
                    this._fnMetaImageSrc = src;
                    this._fnMetaImageReady = false;
                    img.src = src;
                }
            }
            this.setDirtyCanvas(true, true);
        };
    },
});

