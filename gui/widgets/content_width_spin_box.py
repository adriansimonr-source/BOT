from PySide6.QtCore import QRect
from PySide6.QtWidgets import QSpinBox, QStyle, QStyleOptionSpinBox


class ContentWidthSpinBox(QSpinBox):
    def sizeHint(self):
        hint = super().sizeHint()
        hint.setWidth(self._required_width())
        return hint

    def minimumSizeHint(self):
        hint = super().minimumSizeHint()
        hint.setWidth(self._required_width())
        return hint

    def _required_width(self):
        metrics = self.fontMetrics()
        text_width = max(
            metrics.horizontalAdvance(
                f"{self.prefix()}{self.textFromValue(value)}{self.suffix()}"
            )
            for value in (self.minimum(), self.maximum())
        )

        probe_width = 1000
        option = QStyleOptionSpinBox()
        self.initStyleOption(option)
        option.rect = QRect(
            0,
            0,
            probe_width,
            max(super().sizeHint().height(), 1),
        )
        editor = self.style().subControlRect(
            QStyle.ComplexControl.CC_SpinBox,
            option,
            QStyle.SubControl.SC_SpinBoxEditField,
            self,
        )
        chrome_width = max(0, probe_width - editor.width())
        return text_width + chrome_width + 4
