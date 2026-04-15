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
                self.setSize(sz);
                self.setDirtyCanvas(true, true);
            });
        };
    },
});

