from langchain_core.tools import BaseTool
from typing import Optional, Type
from paddleocr import PaddleOCR
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
import os


class OcrTool(BaseTool):
    name: str = "ocr_tool"
    description: str = """当需要识别图像文件，且文件格式为[".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".ico", ".jfif", ".webp", ".svg",".pdf"]，可以通过本工具从图像文件中提取文本，该工具输入文件名称，输出文件文本内容"""

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        try:
            import paddleocr
        except ImportError:
            raise ImportError(
                "Could not import paddleocr python package. "
                "Please install it with `pip install paddleocr`."
            )
        path = os.path.join(os.getcwd(), "uploaded_files")
        file = os.path.join(path, query)
        ocr = PaddleOCR(use_angle_cls=True, lang="ch")
        result = ocr.ocr(file, cls=True)
        text = ""
        for idx in range(len(result)):
            res = result[idx]
            text += res[1][0]
        return text
