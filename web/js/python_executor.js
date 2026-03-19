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

    // Find all slots with the prefix
    let customSlots = slots.filter(s => s.name.startsWith(prefix));
    
    // Find the index of the LAST connected slot among custom slots
    let lastConnectedSlotIndex = -1;
    for (let i = 0; i < customSlots.length; i++) {
        if (customSlots[i].link !== null && customSlots[i].link !== undefined) {
            lastConnectedSlotIndex = i;
        }
    }

    // Required count: at least 2, and exactly one empty slot after the last connected one.
    let requiredSlotsCount = Math.max(2, lastConnectedSlotIndex + 2);
    requiredSlotsCount = Math.min(requiredSlotsCount, maxSlots);

    // Trim empty slots from the end until we reach the required count
    while (true) {
        let currentCustomSlots = (type === 1 ? node.inputs : node.outputs).filter(s => s.name.startsWith(prefix));
        if (currentCustomSlots.length <= requiredSlotsCount) break;

        // Find the absolute LAST slot index in the node's full list that matches the prefix
        let lastSlotIndexInNode = -1;
        let allSlots = type === 1 ? node.inputs : node.outputs;
        for (let i = allSlots.length - 1; i >= 0; i--) {
            if (allSlots[i].name.startsWith(prefix)) {
                lastSlotIndexInNode = i;
                break;
            }
        }

        if (lastSlotIndexInNode !== -1) {
            let lastSlot = allSlots[lastSlotIndexInNode];
            // Only remove if it's the very last custom slot and it's empty
            if (lastSlot.link === null || lastSlot.link === undefined) {
                if (type === 1) node.removeInput(lastSlotIndexInNode);
                else node.removeOutput(lastSlotIndexInNode);
            } else {
                // If the last slot is connected, we can't trim further
                break; 
            }
        } else {
            break;
        }
    }

    // Add necessary slots if we are below required
    customSlots = (type === 1 ? node.inputs : node.outputs).filter(s => s.name.startsWith(prefix));
    let currentSlotsCount = customSlots.length;
    
    while (currentSlotsCount < requiredSlotsCount) {
        // Find the next available index based on current naming pattern in1, in2...
        // We find the highest number currently in use and add 1
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
