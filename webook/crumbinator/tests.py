import pytest
from webook.crumbinator.crumb_node import CrumbNode


def test_crumb_node_icon_html():
    node = CrumbNode(
        title="Something",
        url="#",
        icon_class="fas fa-question-circle",
    )
    
    assert node.icon_html == "<i class='fas fa-question-circle'></i> "


def test_crumb_node_joined_html_classes():
    node = CrumbNode(
        title="Something",
        url="#",
        html_classes=["class1", "class2", "class3", "class4"]
    )

    assert node.joined_html_classes == "class1 class2 class3 class4"

def test_crumb_node_as_html():
    node = CrumbNode(
        title="Something",
        url="#",
        html_classes=["class1", "class2", "class3"],
        icon_class="fas fa-question-circle"
    )

    assert node.as_html == "<a href='#' class='class1 class2 class3'><i class='fas fa-question-circle'></i> Something</a>"
