from django import template
from django.template import Context
from django.template.loader import get_template
from anytree import Node, PreOrderIter

register = template.Library()


@register.filter(name="crumbinator")
def crumbinator(tree: Node):
    
    unpacked_tree = [node for node in PreOrderIter(tree)]
    top_level_nodes = []
    
    # We need to walk through the sibling nodes, and set a flag to make sure that they are 
    # not treated as normal "top-level" crumbs.
    for node in unpacked_tree:
        top_level_nodes.append(node)
        if len(node.siblings) > 0:
            for f in node.siblings:
                if f not in top_level_nodes:
                    f.skip_render = True

    top_level_nodes[-1].is_active = True

    ctx = Context(
        {
            "tree": unpacked_tree
        }
    ).flatten()

    template = get_template("mdbootstrap_crumbs.html")
    
    return template.render(ctx)