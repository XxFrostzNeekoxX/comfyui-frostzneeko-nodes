import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

/*
 * FrostzNeeko — FNPromptFromFile counter bridge
 */

app.registerExtension({
    name: "FrostzNeeko.PromptFromFileCounter",

    async beforeRegisterNodeDef(nodeType, nodeData, _app) {
        if (nodeData.name !== "FNPromptFromFile") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;

        nodeType.prototype.onNodeCreated = function () {
            originalOnNodeCreated?.call(this);

            let counter = 0;
            const countWidget = this.widgets?.find((w) => w.name === "count");
            if (!countWidget) return;

            // Keep `count` available for backend, but hide from UI.
            countWidget.type = "converted-widget";
            countWidget.serializeValue = () => counter++;

            api.addEventListener("promptQueued", () => {
                counter = 0;
            });
        };
    },
});

