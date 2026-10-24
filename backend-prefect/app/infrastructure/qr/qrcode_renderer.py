import base64
import io

import qrcode

from ...application.ports import QrCodeRenderer


class PngQrCodeRenderer(QrCodeRenderer):
    def png_base64(self, data: str) -> str:
        buf = io.BytesIO()
        qrcode.make(data).save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
