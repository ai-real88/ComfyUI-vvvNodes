from .nodes import CustomSlider, PythonExecutorNode, UniversalJSONNode_vvv, SimpleJSONNode_vvv

NODE_CLASS_MAPPINGS = {
    "CustomSlider_vvv": CustomSlider,
    "PythonExecutorNode_vvv": PythonExecutorNode,
    "UniversalJSONNode_vvv": UniversalJSONNode_vvv,
    "SimpleJSONNode_vvv": SimpleJSONNode_vvv
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomSlider_vvv": "🎚️ Custom Slider (vvvNodes)",
    "PythonExecutorNode_vvv": "🐍 Python Code Executor (vvvNodes)",
    "UniversalJSONNode_vvv": "Universal JSON (vvvNodes)",
    "SimpleJSONNode_vvv": "JSON (vvvNodes)"
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
