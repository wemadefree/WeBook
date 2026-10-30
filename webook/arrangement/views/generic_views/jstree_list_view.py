from django.urls import reverse

from webook.arrangement.views.generic_views.json_list_view import JsonListView


class JSTreeListView(JsonListView):
    """JSTreeListView valid for models with the nested mixin applied
    This returns a JSON document which can be given to JSTREE and used to render a tree.
    """

    inject_resolved_crudl_urls_into_nodes = False

    def get_queryset(self):
        if not hasattr(self, "model") or not self.model:
            raise Exception("Valid model must be set")
        if not hasattr(self.model, "parent") or not hasattr(
            self.model, "nested_children"
        ):
            raise Exception(
                "Attributes parent or nested_children are not present on model"
            )

        nodes = self.model.node_list()

        if self.inject_resolved_crudl_urls_into_nodes:
            self._process_urls(nodes)

        return nodes

    def _process_urls(self, nodes):
        urls = [
            ("detail_url", self.section.crudl_map.detail_url),
            ("edit_url", self.section.crudl_map.edit_url),
            ("delete_url", self.section.crudl_map.delete_url),
            ("archive_url", self.section.crudl_map.archive_url),
        ]
        for item in nodes:
            for attr_name, url in urls:
                if url:
                    item["data"][attr_name] = reverse(
                        url, kwargs={"slug": item["data"]["slug"]}
                    )
            if "children" in item:
                self._process_urls(item["children"])
