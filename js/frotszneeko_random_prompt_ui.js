import { app } from "../../scripts/app.js";

/*
 * FrostzNeeko — Random Prompt Generator: mascot + generated_prompt textbox (same UX as Prompt From File)
 */

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
        console.warn("[FrostzNeeko] Could not load mascot (random prompt)");
        mascotImg = null;
    };
    mascotImg.src = "/FrostzNeeko/mascot?v=" + Date.now();
}
ensureMascotLoaded();

const IMG_BLOCK_H = 160;

app.registerExtension({
    name: "FrostzNeeko.RandomPromptGeneratorDisplay",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNRandomPromptGenerator") return;

        const origExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (data) {
            origExecuted?.apply(this, arguments);
            if (!data) return;
            if (data.generated_prompt?.length > 0) {
                const w = this.widgets?.find((w) => w.name === "generated_prompt");
                if (w) w.value = data.generated_prompt[0] || "";
            }
            this.setDirtyCanvas(true, true);
        };

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);

            const spacer = {
                name: "fn_mascot_spacer",
                type: "custom",
                value: null,
                options: { serialize: false },
                computeSize: () => [200, IMG_BLOCK_H],
                draw: () => {},
            };

            if (this.widgets) {
                this.widgets.unshift(spacer);
            }

            const self = this;
            requestAnimationFrame(() => {
                const computed = self.computeSize();
                computed[0] = Math.max(computed[0], 400);
                self.setSize(computed);
                self.setDirtyCanvas(true, true);
            });
        };

        const origFg = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            origFg?.apply(this, arguments);
            if (this.flags?.collapsed) return;
            if (!mascotImg || !mascotLoaded) return;

            const spacer = this.widgets?.find((w) => w.name === "fn_mascot_spacer");
            if (!spacer) return;

            const y = spacer.last_y ?? 0;
            const nodeW = this.size[0];
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
