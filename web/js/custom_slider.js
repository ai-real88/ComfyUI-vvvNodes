import { app } from "/scripts/app.js";

const COMFY_COLORS = {
    "default": undefined,
    "red": "#533",
    "brown": "#593930",
    "green": "#353",
    "blue": "#335",
    "purple": "#323",
    "cyan": "#233",
    "yellow": "#442",
    "orange": "#532",
    "pink": "#534",
    "black": "#222"
};

app.registerExtension({
    name: "vvvNodes.CustomSlider",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "CustomSlider_vvv") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                const node = this;

                setTimeout(() => {
                    const valueWidget = node.widgets.find((w) => w.name === "value");
                    const minWidget = node.widgets.find((w) => w.name === "min_val");
                    const maxWidget = node.widgets.find((w) => w.name === "max_val");
                    const stepWidget = node.widgets.find((w) => w.name === "step");
                    const precisionWidget = node.widgets.find((w) => w.name === "precision");
                    const tooltipWidget = node.widgets.find((w) => w.name === "tooltip");
                    const colorWidget = node.widgets.find((w) => w.name === "slider_color");

                    if (!valueWidget || !minWidget || !maxWidget || !stepWidget || !precisionWidget) {
                        return;
                    }

                    const originalValueCallback = valueWidget.callback;
                    let isReentrant = false;

                    valueWidget.callback = function(val) {
                         if (isReentrant) return;
                         
                         const min = parseFloat(minWidget.value) || 0;
                         const max = parseFloat(maxWidget.value) || 1;
                         const step = parseFloat(stepWidget.value) || 0.01;
                         const prec = parseInt(precisionWidget.value, 10) || 0;

                         let currentVal = parseFloat(val);
                         if (isNaN(currentVal)) currentVal = min;
                         
                         // Manually snap to our mathematical step relative to 0
                         currentVal = Math.round(currentVal / step) * step;

                         // Clamp
                         if (currentVal < min) currentVal = min;
                         if (currentVal > max) currentVal = max;

                         // Lock precision
                         currentVal = parseFloat(currentVal.toFixed(prec));
                         
                         isReentrant = true;
                         valueWidget.value = currentVal; // set it back into the widget
                         if (originalValueCallback) originalValueCallback.apply(this, [currentVal]);
                         isReentrant = false;
                         
                         if (app.graph) app.graph.setDirtyCanvas(true, true);
                    };

                    // Force options object if missing
                    valueWidget.options = valueWidget.options || {};
                    
                    Object.defineProperty(valueWidget.options, "min", {
                        get: () => parseFloat(minWidget.value) || 0,
                        configurable: true
                    });
                    
                    Object.defineProperty(valueWidget.options, "max", {
                        get: () => parseFloat(maxWidget.value) || 1,
                        configurable: true
                    });

                    Object.defineProperty(valueWidget.options, "precision", {
                        get: () => parseInt(precisionWidget.value, 10) || 0,
                        configurable: true
                    });

                    // Add a tooltip getter for subgraph compatibility
                    Object.defineProperty(valueWidget, "tooltip", {
                        get: () => tooltipWidget ? tooltipWidget.value : "",
                        configurable: true
                    });
                    Object.defineProperty(valueWidget.options, "tooltip", {
                        get: () => tooltipWidget ? tooltipWidget.value : "",
                        configurable: true
                    });

                    const enforceBounds = () => {
                        // Apply Dark ComfyUI standard colors
                        if (colorWidget) {
                            let colorName = colorWidget.value;
                            let hex = COMFY_COLORS[colorName];
                            valueWidget.color = hex;
                            valueWidget.options.slider_color = hex;
                            valueWidget.options.marker_color = hex; 
                        }

                        // Trigger the value widget callback manually to resolve bounds
                        if (valueWidget.callback) {
                            valueWidget.callback(valueWidget.value);
                        }
                    };

                    const widgetsToWatch = [minWidget, maxWidget, stepWidget, precisionWidget, tooltipWidget, colorWidget].filter(Boolean);
                    
                    // Hook into settings callbacks
                    for (const w of widgetsToWatch) {
                        const originalCallback = w.callback;
                        w.callback = function() {
                            if (originalCallback) originalCallback.apply(this, arguments);
                            enforceBounds();
                        };
                    }

                    // Initial sync
                    enforceBounds();

                }, 200);

                return r;
            };
        }
    }
});
