import json
class CustomSlider:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "value": ("FLOAT", {"display": "slider", "default": 0.5, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 0.01}),
                "min_val": ("FLOAT", {"default": 0.0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 0.1}),
                "max_val": ("FLOAT", {"default": 1.0, "min": -0xffffffffffffffff, "max": 0xffffffffffffffff, "step": 0.1}),
                "step": ("FLOAT", {"default": 0.01, "min": 0.0001, "max": 1000.0, "step": 0.01}),
                "precision": ("INT", {"default": 2, "min": 0, "max": 10, "step": 1}),
                "slider_color": (["default", "red", "green", "blue", "yellow", "purple", "cyan", "orange", "pink"], {"default": "default"}),
                "tooltip": ("STRING", {"default": ""}),
            },
        }

    RETURN_TYPES = ("FLOAT", "INT",)
    RETURN_NAMES = ("FLOAT", "INT",)
    FUNCTION = "execute"
    CATEGORY = "vvvNodes/math"

    def execute(self, value, min_val, max_val, step, precision, slider_color, tooltip):
        # We ensure standard precision mathematically on the Python side
        if precision > 0:
            value = round(value, precision)
        else:
            value = round(value)

        # Clamping to limits in case JS missed it
        value = max(min_val, min(max_val, value))

        return (value, int(value),)


# Специальный класс-заглушка для ComfyUI, который "соглашается" соединяться с любым типом данных
class AnyType(str):
    def __ne__(self, __value: object) -> bool:
        return False

# Инициализируем ANY-тип
ANY = AnyType("*")


class PythonExecutorNode:
    """
    Нода для выполнения произвольного Python кода.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        optional_inputs = {f"in{i}": (ANY, ) for i in range(1, 17)}
        return {
            "required": {
                # Текстовое поле для ввода кода
                "python_code": ("STRING", {
                    "multiline": True,
                    "default": "# Доступные функции: torch, math, np\n# Входы: in1..in16\n# Назначьте результат переменным out1..out16\n\nout1 = in1"
                }),
            },
            "optional": optional_inputs,
            "hidden": {
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    # Возвращаем тоже любые типы (можно сделать несколько выходов)
    RETURN_TYPES = tuple([ANY] * 16)
    RETURN_NAMES = tuple([f"out{i}" for i in range(1, 17)])
    FUNCTION = "execute_code"
    CATEGORY = "vvvNodes/Scripting"

    def execute_code(self, python_code, extra_pnginfo=None, unique_id=None, **kwargs):
        input_labels = {}
        output_labels = {}
        if extra_pnginfo and "workflow" in extra_pnginfo and unique_id:
            for node in extra_pnginfo["workflow"].get("nodes", []):
                if str(node.get("id")) == str(unique_id):
                    for inp in node.get("inputs", []):
                        if inp.get("label"):
                            input_labels[inp["name"]] = inp["label"]
                    for out in node.get("outputs", []):
                        if out.get("label"):
                            output_labels[out["name"]] = out["label"]
                    break

        # Словарь локальных переменных, которые будут доступны вашему коду
        local_vars = {}
        for i in range(1, 17):
            orig_in = f"in{i}"
            orig_out = f"out{i}"
            
            val = kwargs.get(orig_in, None)
            local_vars[orig_in] = val
            if orig_in in input_labels:
                local_vars[input_labels[orig_in]] = val
                
            local_vars[orig_out] = None
            if orig_out in output_labels:
                local_vars[output_labels[orig_out]] = None
        
        # Импортируем популярные библиотеки, чтобы они были доступны внутри виджета по умолчанию
        import torch
        import math
        import numpy as np
        
        # Глобальное окружение для нашего скрипта
        global_vars = {
            "torch": torch,
            "math": math,
            "np": np,
             # Можно добавить встроенные питоновские функции (abs, len и т.д.)
            "__builtins__": __builtins__
        }

        try:
            # Магия Python: динамическое выполнение строки кода
            exec(python_code, global_vars, local_vars)
        except Exception as e:
            # Если в введенном коде ошибка - прерываем генерацию и выводим лог
            raise RuntimeError(f"Ошибка выполнения Python кода в ноде: {e}")

        # Возвращаем результаты, которые скрипт присвоил переменным out1..out16
        res = []
        for i in range(1, 17):
            orig_out = f"out{i}"
            out_val = local_vars.get(orig_out)
            if orig_out in output_labels:
                custom_val = local_vars.get(output_labels[orig_out])
                if custom_val is not None:
                    out_val = custom_val
            res.append(out_val)
            
        return tuple(res)


def safe_dict_copy(d):
    if isinstance(d, dict):
        return {k: safe_dict_copy(v) for k, v in d.items()}
    return d


class UniversalJSONNode_vvv:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key_path": ("STRING", {"default": "settings.value"}),
                "default_on_read": ("STRING", {"default": ""}), 
                "value": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "pipe (any)": (ANY, ),
                "value (any)": (ANY, ),
            }
        }

    RETURN_TYPES = (ANY, "STRING", "BOOLEAN", ANY, "STRING", "INT", "FLOAT", "BOOLEAN")
    RETURN_NAMES = ("pipe (any)", "pipe (json)", "found", "value (any)", "value (str)", "value (int)", "value (float)", "value (bool)")
    FUNCTION = "execute"
    CATEGORY = "vvvNodes/JSON"
    OUTPUT_NODE = True 

    def execute(self, key_path, value, default_on_read, **kwargs):
        errors =[]
        json_input = kwargs.get("pipe (any)", None)
        data = {}

        if json_input is not None:
            if isinstance(json_input, str):
                if json_input.strip():
                    try:
                        data = json.loads(json_input)
                    except Exception as e:
                        errors.append(f"❌ Input Parse Error: {e}")
            elif isinstance(json_input, dict):
                data = safe_dict_copy(json_input)
            else:
                try:
                    data = dict(json_input)
                except (TypeError, ValueError):
                    if hasattr(json_input, '__dict__'):
                        data = safe_dict_copy(json_input.__dict__)
                    else:
                        errors.append("❌ Invalid json input type.")

        keys = [k for k in key_path.split('.') if k]
        
        curr_check = data
        found_in_input = True
        if not data:
            found_in_input = False
        elif keys:
            for k in keys:
                if isinstance(curr_check, dict) and k in curr_check:
                    curr_check = curr_check[k]
                else:
                    found_in_input = False
                    break
        
        write_mode = False
        val_to_write = None

        if "value (any)" in kwargs:
            write_mode = True
            val_to_write = kwargs["value (any)"]
        elif value.strip() != "":
            write_mode = True
            try:
                # Interpret "" as an empty string
                if value.strip() == '""':
                    val_to_write = ""
                else:
                    val_to_write = json.loads(value)
            except:
                val_to_write = value

        if write_mode and keys:
            curr = data
            for k in keys[:-1]:
                if k not in curr or not isinstance(curr[k], dict):
                    curr[k] = {}
                curr = curr[k]
            curr[keys[-1]] = val_to_write 

        curr = data
        found_now = True
        if keys:
            for k in keys:
                if isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    found_now = False
                    break
        
        # Determine source prefix for preview
        source_prefix = "found: " if found_now else "default: "
        if write_mode and found_now:
            source_prefix = "value: "

        # Normalize default_on_read if it is exactly ""
        effective_default = "" if default_on_read == '""' else default_on_read

        # Strict check: if not found and both fallback options are empty
        if not found_now and default_on_read == "" and value == "":
            raise ValueError(f"❌ Key path '{key_path}' not found and no fallback value provided in 'default_on_read' or 'value'.")

        out_val = curr if found_now else effective_default

        preview_data = ""
        if errors:
            preview_data = "\n".join(errors)
        else:
            if isinstance(out_val, (dict, list)):
                try:
                    preview_data = json.dumps(out_val, indent=2, default=str)
                except:
                    preview_data = str(out_val)
            else:
                preview_data = str(out_val)
        
        preview_text = f"{source_prefix}{preview_data}"

        out_json_any = data
        out_json_str = json.dumps(data, default=str, indent=2)
        out_str = str(out_val) if out_val is not None else ""
        
        out_float = 0.0
        try: out_float = float(out_val)
        except (ValueError, TypeError): pass
            
        out_int = 0
        try: out_int = int(out_val)
        except (ValueError, TypeError):
            try: out_int = int(float(out_val))
            except (ValueError, TypeError): pass
                
        out_bool = False
        if isinstance(out_val, bool):
            out_bool = out_val
        elif isinstance(out_val, str):
            out_bool = out_val.strip().lower() in ("true", "1", "yes", "on", "t", "y")
        else:
            out_bool = bool(out_val)

        return {
            "ui": {"text": [preview_text]}, 
            "result": (out_json_any, out_json_str, found_in_input, out_val, out_str, out_int, out_float, out_bool)
        }


class SimpleJSONNode_vvv:
    """
    Lenient version with 'found' output. Does not stop on error.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key_path": ("STRING", {"default": "settings.value"}),
            },
            "optional": {
                "pipe (any)": (ANY, ),
                "value (any)": (ANY, ),
            }
        }

    RETURN_TYPES = (ANY, ANY, "BOOLEAN")
    RETURN_NAMES = ("pipe (any)", "value (any)", "found")
    FUNCTION = "execute"
    CATEGORY = "vvvNodes/JSON"

    def execute(self, key_path, **kwargs):
        json_input = kwargs.get("pipe (any)", None)
        data = {}

        if json_input is not None:
            if isinstance(json_input, str):
                if json_input.strip():
                    try:
                        data = json.loads(json_input)
                    except:
                        pass
            elif isinstance(json_input, dict):
                data = safe_dict_copy(json_input)
            else:
                try:
                    data = dict(json_input)
                except:
                    if hasattr(json_input, '__dict__'):
                        data = safe_dict_copy(json_input.__dict__)

        keys = key_path.split('.')
        
        curr_check = data
        found_in_input = True
        if not data:
            found_in_input = False
        else:
            for k in keys:
                if isinstance(curr_check, dict) and k in curr_check:
                    curr_check = curr_check[k]
                else:
                    found_in_input = False
                    break
        
        if "value (any)" in kwargs:
            val_to_write = kwargs["value (any)"]
            curr = data
            for k in keys[:-1]:
                if k not in curr or not isinstance(curr[k], dict):
                    curr[k] = {}
                curr = curr[k]
            curr[keys[-1]] = val_to_write 

        curr = data
        found_now = True
        for k in keys:
            if isinstance(curr, dict) and k in curr:
                curr = curr[k]
            else:
                found_now = False
                break
        
        out_val = curr if found_now else None

        return (data, out_val, found_in_input)


class StrictJSONNode_vvv:
    """
    Strict version without 'found' output. Stops on missing key.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "key_path": ("STRING", {"default": "settings.value"}),
            },
            "optional": {
                "pipe (any)": (ANY, ),
                "value (any)": (ANY, ),
            }
        }

    RETURN_TYPES = (ANY, ANY)
    RETURN_NAMES = ("pipe (any)", "value (any)")
    FUNCTION = "execute"
    CATEGORY = "vvvNodes/JSON"

    def execute(self, key_path, **kwargs):
        json_input = kwargs.get("pipe (any)", None)
        data = {}

        if json_input is not None:
            if isinstance(json_input, str):
                if json_input.strip():
                    try:
                        data = json.loads(json_input)
                    except:
                        pass
            elif isinstance(json_input, dict):
                data = safe_dict_copy(json_input)
            else:
                try:
                    data = dict(json_input)
                except:
                    if hasattr(json_input, '__dict__'):
                        data = safe_dict_copy(json_input.__dict__)

        keys = key_path.split('.')
        
        # Check if exists (strict mode)
        curr = data
        found = True
        if not data and "value (any)" not in kwargs:
            found = False
        else:
            for k in keys:
                if isinstance(curr, dict) and k in curr:
                    curr = curr[k]
                else:
                    found = False
                    break
        
        if "value (any)" in kwargs:
            val_to_write = kwargs["value (any)"]
            curr = data
            for k in keys[:-1]:
                if k not in curr or not isinstance(curr[k], dict):
                    curr[k] = {}
                curr = curr[k]
            curr[keys[-1]] = val_to_write 
            found = True

        if not found:
            raise ValueError(f"❌ Key path '{key_path}' not found in JSON.")

        return (data, curr)

