import { app } from "../../scripts/app.js";

/*
 * FrostzNeeko — Random Prompt Generator: updates generated_prompt textbox after run (no mascot).
 */

app.registerExtension({
    name: "FrostzNeeko.RandomPromptGeneratorDisplay",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNRandomPromptGenerator") return;

        const origExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (data) {
            origExecuted?.apply(this, arguments);
            if (!data) return;
            const gp = data.generated_prompt;
            const text = Array.isArray(gp) ? (gp[0] ?? "") : typeof gp === "string" ? gp : "";
            if (text) {
                const w = this.widgets?.find((w) => w.name === "generated_prompt");
                if (w) {
                    w.value = text;
                    if (typeof w.callback === "function") w.callback(text);
                }
            }
            this.setDirtyCanvas(true, true);
        };

        const origCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            origCreated?.apply(this, arguments);
            const self = this;
            requestAnimationFrame(() => {
                const computed = self.computeSize();
                computed[0] = Math.max(computed[0], 400);
                self.setSize(computed);
                self.setDirtyCanvas(true, true);
            });
        };
    },
});
