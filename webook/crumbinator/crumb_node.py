from __future__ import annotations
from typing import Callable
from anytree import NodeMixin
from typing import List


class CrumbNode(NodeMixin):
    """
        Node representing a breadcrumb
    """

    def __init__(self, title:str, url:Callable, icon_class:str=None, html_classes:List[str]=None, parent:CrumbNode=None, is_active:bool=False) -> None:
        """
            Initialize the CrumbNode

            :param title: The 'friendly' name of the node, will be shown in front-end to the user
            :type title: str

            :param url: The URL that this crumb leads to
            :type url: str

            :param icon_class: Class to use in the icon, for instance 'fas fa-question-circle'
            :type icon_class: str

            :param html_classes: A list of strings to be used as html classes for the link tag
            :type html_classes: List[str]

            :param parent: The parent of the current node
            :type parent: CrumbNode

            :param is_active: Designates if this crumb is the active crumb, in which case special styling may apply. Default behaviour is for the last 
                              top level node to be automatically flagged as active, so seldom should you set anything but false here.
            :type is_active: bool
        """
        self.title = title
        self.url = url
        self.html_classes = html_classes if html_classes is not None else list()
        self.parent = parent
        self.icon_class = icon_class
        self.is_active = is_active

    @property
    def icon_html(self) -> str:
        """
            Returns a string containing html for the icon.
            Example:
                <i class='fas fa-question-circle'></i>
            If icon_class is not set then an empty string will be returned
        """
        return f"<i class='{self.icon_class}'></i> " if self.icon_class is not None else ""

    @property
    def joined_html_classes(self) -> str:
        """
            Returns a string with html classes joined together, from the attribute html_classes.
        """
        return ' '.join(self.html_classes)

    @property
    def as_html(self) -> str:
        """
            Returns a string of html, which is the current node converted to a link tag (a).
        """
        return f"<a href='{self.url}' class='{self.joined_html_classes}'>{self.icon_html}{self.title}</a>"

    def __str__(self) -> str:
        return self.title