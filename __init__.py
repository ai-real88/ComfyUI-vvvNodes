from .nodes import CustomSlider, PythonExecutorNode

NODE_CLASS_MAPPINGS = {
    "CustomSlider_vvv": CustomSlider,
    "PythonExecutorNode_vvv": PythonExecutorNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CustomSlider_vvv": "🎚️ Custom Slider (vvvNodes)",
    "PythonExecutorNode_vvv": "🐍 Python Code Executor (vvvNodes)"
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
