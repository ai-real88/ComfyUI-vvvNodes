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
        return {
            "required": {
                # Текстовое поле для ввода кода
                "python_code": ("STRING", {
                    "multiline": True,
                    "default": "# Доступные функции: torch, math, np\n# Входы: in1, in2, in3\n# Назначьте результат переменным out1 и/или out2\n\nout1 = in1"
                }),
            },
            "optional": {
                # Опциональные входы (можно подать картинки, числа, латенты)
                "in1": (ANY, ),
                "in2": (ANY, ),
                "in3": (ANY, ),
            }
        }

    # Возвращаем тоже любые типы (можно сделать несколько выходов)
    RETURN_TYPES = (ANY, ANY)
    RETURN_NAMES = ("out1", "out2")
    FUNCTION = "execute_code"
    CATEGORY = "vvvNodes/Scripting"

    def execute_code(self, python_code, in1=None, in2=None, in3=None):
        # Словарь локальных переменных, которые будут доступны вашему коду
        local_vars = {
            "in1": in1,
            "in2": in2,
            "in3": in3,
            "out1": None,
            "out2": None,
        }
        
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

        # Возвращаем результаты, которые скрипт присвоил переменным out1 и out2
        return (local_vars.get("out1"), local_vars.get("out2"))
