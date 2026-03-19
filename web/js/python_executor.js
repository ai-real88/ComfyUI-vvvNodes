import { app } from "/scripts/app.js";

app.registerExtension({
    name: "vvv.PythonExecutorNode",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "PythonExecutorNode_vvv") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                // Keep trying to apply dynamic connections shortly after creation
                // so that when loaded from a workflow, restoring links doesn't mess things up.
                setTimeout(() => {
                    dynamicConnections(this, "in", 1);
                    dynamicConnections(this, "out", 2);
                }, 10);
                setTimeout(() => {
                    dynamicConnections(this, "in", 1);
                    dynamicConnections(this, "out", 2);
                }, 100);
                
                return r;
            };

            const onConnectionsChange = nodeType.prototype.onConnectionsChange;
            nodeType.prototype.onConnectionsChange = function (type, index, connected, link_info) {
                const r = onConnectionsChange ? onConnectionsChange.apply(this, arguments) : undefined;
                
                // type = 1 for INPUT, 2 for OUTPUT
                if (type === 1) {
                    dynamicConnections(this, "in", 1);
                } else if (type === 2) {
                    dynamicConnections(this, "out", 2);
                }
                
                return r;
            };

            // Custom slot name renaming handler to use 'label' property 
            // instead of 'name' parameter index property which would break validation.
            nodeType.prototype.renameInput = function(slot, text) {
                if (this.inputs[slot]) {
                    this.inputs[slot].label = text;
                    this.setDirtyCanvas(true);
                }
            };
            nodeType.prototype.renameOutput = function(slot, text) {
                if (this.outputs[slot]) {
                    this.outputs[slot].label = text;
                    this.setDirtyCanvas(true);
                }
            };
            
        }
    }
});

function dynamicConnections(node, prefix, type) {
    const maxSlots = 16;
    let slots = type === 1 ? node.inputs : node.outputs;
    if (!slots) return;

    // Determine the required number of slots: count how many are connected and add 1, min 2, max 16.
    let customSlots = slots.filter(s => s.name.startsWith(prefix));
    let connectedCount = customSlots.filter(s => s.link !== null && s.link !== undefined).length;
    let requiredSlotsCount = Math.max(2, connectedCount + 1);
    requiredSlotsCount = Math.min(requiredSlotsCount, maxSlots);

    // Trim empty slots from the end until we reach the required count
    while (true) {
        let currentCustomCount = (type === 1 ? node.inputs : node.outputs).filter(s => s.name.startsWith(prefix)).length;
        if (currentCustomCount <= requiredSlotsCount) break;

        // Find the LAST custom slot
        let lastCustomIndex = -1;
        let lastCustomSlot = null;
        let currentSlots = type === 1 ? node.inputs : node.outputs;
        for (let i = currentSlots.length - 1; i >= 0; i--) {
            if (currentSlots[i].name.startsWith(prefix)) {
                lastCustomIndex = i;
                lastCustomSlot = currentSlots[i];
                break;
            }
        }

        if (lastCustomIndex !== -1 && (lastCustomSlot.link === null || lastCustomSlot.link === undefined)) {
            // The last custom slot is empty and we have more than required slots, so remove it.
            if (type === 1) node.removeInput(lastCustomIndex);
            else node.removeOutput(lastCustomIndex);
        } else {
            // The last custom slot is connected, so we can't remove from the end anymore!
            break; 
        }
    }

    // Add necessary slots if we are below required
    customSlots = (type === 1 ? node.inputs : node.outputs).filter(s => s.name.startsWith(prefix));
    let currentSlotsCount = customSlots.length;
    
    while (currentSlotsCount < requiredSlotsCount) {
        // Find the next available index
        let nextIndex = 1;
        for (const s of customSlots) {
            const match = s.name.match(new RegExp(`^${prefix}(\\d+)$`));
            if (match) {
                const num = parseInt(match[1]);
                if (num >= nextIndex) nextIndex = num + 1;
            }
        }
        
        // If match fails or something, fallback
        let newName = prefix + nextIndex;
        if (type === 1) {
            node.addInput(newName, "*");
        } else {
            node.addOutput(newName, "*");
        }
        
        // Refresh customSlots count
        customSlots = (type === 1 ? node.inputs : node.outputs).filter(s => s.name.startsWith(prefix));
        currentSlotsCount = customSlots.length;
    }
}
