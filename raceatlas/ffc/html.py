"""Small bounded HTML reader for the supported labeled-field dialect.

This is deliberately not a browser or a best-effort general HTML repair engine.
Unexpected nesting/duplicate fact fields must not silently change source facts.
"""

from dataclasses import dataclass, field
from html.parser import HTMLParser

from .types import AdapterError

VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())


@dataclass
class Node:
    tag: str
    attrs: dict[str, str]
    children: list = field(default_factory=list)

    @property
    def text(self):
        if self.tag in {"script", "style", "noscript"}:
            return ""
        return " ".join(
            " ".join(
                item.text if isinstance(item, Node) else item for item in self.children
            ).split()
        )

    def all(self, predicate):
        result = []
        for child in self.children:
            if isinstance(child, Node):
                if predicate(child):
                    result.append(child)
                result.extend(child.all(predicate))
        return result

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()


class Reader(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document", {})
        self.stack = [self.root]
        self.count = 0

    def handle_starttag(self, tag, attrs):
        self.count += 1
        if self.count > 20000 or len(self.stack) > 100:
            raise AdapterError("html_limit", "html", "Document structure exceeds parser limits")
        if len(dict(attrs)) != len(attrs):
            raise AdapterError("html_attributes", "html", "Duplicate HTML attributes")
        node = Node(tag, {key: value or "" for key, value in attrs})
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if len(self.stack) == 1 or self.stack[-1].tag != tag:
            raise AdapterError("html_structure", "html", "Unexpected closing tag")
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def read_html(html):
    if not isinstance(html, str) or len(html) > 2_000_000:
        raise AdapterError("html_limit", "html", "Expected bounded HTML text")
    parser = Reader()
    parser.feed(html)
    parser.close()
    if len(parser.stack) != 1:
        raise AdapterError("html_structure", "html", "Unclosed document elements")
    return parser.root


def single(nodes, field):
    if len(nodes) != 1:
        raise AdapterError("layout_changed", field, "Expected exactly one fact container")
    return nodes[0]


def by_id(root, identifier):
    return single(root.all(lambda node: node.attrs.get("id") == identifier), identifier)


def labeled_fields(node):
    """Direct dt/dd pairs only: nested lists cannot donate facts to their parent."""
    fields = {}
    children = [child for child in node.children if isinstance(child, Node)]
    if len(children) % 2:
        raise AdapterError("layout_changed", "fields", "Expected paired labels and values")
    for index in range(0, len(children), 2):
        label, value = children[index : index + 2]
        if label.tag != "dt" or value.tag != "dd" or not label.text or not value.text:
            raise AdapterError("layout_changed", "fields", "Invalid label/value pair")
        key = label.text.casefold()
        if key in fields:
            raise AdapterError("duplicate_field", key, "Repeated source fact")
        fields[key] = value.text
    return fields
