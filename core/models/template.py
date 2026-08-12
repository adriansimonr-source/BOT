from dataclasses import dataclass


@dataclass(slots=True)
class Template:
    name: str
    path: str
    template_type: str
    threshold: float = 0.85
    image: object = None

    @property
    def type(self):
        return self.template_type
