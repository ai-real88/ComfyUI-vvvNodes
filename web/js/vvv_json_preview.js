import { app } from "/scripts/app.js";
import { ComfyWidgets } from "/scripts/widgets.js";

console.log("vvvNodes: Loading UniversalJSONNode.Preview extension");

app.registerExtension({
    name: "vvvNodes.UniversalJSONNode.Preview",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "UniversalJSONNode_vvv") {
            console.log("vvvNodes: Registering preview for", nodeData.name);
            const onExecuted = nodeType.prototype.onExecuted;
            
            nodeType.prototype.onExecuted = function(message) {
                console.log("vvvNodes: onExecuted received message", message);
                onExecuted?.apply(this, arguments);

                if (message.text) {
                    let previewWidget = this.widgets?.find(w => w.name === "vvv_preview_text");
                    
                    if (!previewWidget) {
                        console.log("vvvNodes: Creating preview widget");
                        // Use a slightly different name to avoid collisions
                        previewWidget = ComfyWidgets["STRING"](this, "vvv_preview_text", ["STRING", { multiline: true }], app).widget;
                        previewWidget.inputEl.readOnly = true;
                        previewWidget.inputEl.style.opacity = "0.7";
                        previewWidget.inputEl.style.backgroundColor = "transparent";
                    }
                    
                    previewWidget.value = message.text.join("\n");
                    console.log("vvvNodes: Preview updated to", previewWidget.value);
                    this.onResize?.(this.computeSize());
                }
            };
        }
    }
});

