from html import escape as _escape


def _normalize_attr(name, value):
    if value is None:
        return None
    if name == "class_":
        name = "class"
    elif name.endswith("_"):
        name = name[:-1]
    name = name.replace("_", "-")
    return f'{name}="{_escape(str(value), quote=True)}"'


class _Element:
    tag = ""
    self_closing = True

    def __init__(self, **kwargs):
        self.elements = list(kwargs.pop("elements", []) or [])
        self.text = kwargs.pop("text", None)
        self.attrs = kwargs

    def _attrs_str(self):
        parts = []
        for key, value in self.attrs.items():
            attr = _normalize_attr(key, value)
            if attr is not None:
                parts.append(attr)
        return (" " + " ".join(parts)) if parts else ""

    def _children_str(self):
        children = []
        if self.text is not None:
            children.append(_escape(str(self.text)))
        for element in self.elements:
            if hasattr(element, "as_str"):
                children.append(element.as_str())
            else:
                children.append(str(element))
        return "".join(children)

    def as_str(self):
        attrs = self._attrs_str()
        children = self._children_str()
        if children or not self.self_closing:
            return f"<{self.tag}{attrs}>{children}</{self.tag}>"
        return f"<{self.tag}{attrs}/>"


class SVG(_Element):
    tag = "svg"
    self_closing = False


class G(_Element):
    tag = "g"
    self_closing = False


class Path(_Element):
    tag = "path"


class Polygon(_Element):
    tag = "polygon"


class Circle(_Element):
    tag = "circle"


class Ellipse(_Element):
    tag = "ellipse"


class Line(_Element):
    tag = "line"


class Rect(_Element):
    tag = "rect"


class Text(_Element):
    tag = "text"
    self_closing = False

class Title(_Element):
    tag = "title"
    self_closing = False
