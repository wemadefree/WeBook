from typing import Any
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views.generic import DeleteView


class ArchiveView(DeleteView):

    def archive(self, request):
        self.object = self.get_object()
        self.object.archive(request.user.person)

    """
        View for archiving an entity, superceding the DeleteView functionality.
    """

    def delete(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """
        Archive the object by calling archive() method on the fetched object and then
        redirect to success URL
        """

        self.archive(request)
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)


class JsonArchiveView(ArchiveView):
    """
    Same as ArchiveView, but returning a JsonResponse instead of HttpResponseRedirect
    """

    def delete(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        """
        Archive the object by calling archive() method on the fetched object and then
        redirect to success URL
        """
        self.archive(request)
        return JsonResponse({"id": self.object.pk})


class JsonToggleArchiveView(JsonArchiveView):
    """
    Similar to JsonArchiveView, with the important distinction that it toggles the archival state.
    So if the entity is archived it will be un-archived, and vice versa
    """

    def delete(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
        object = self.get_object(self.model.all_objects)

        if object.is_archived:
            object.is_archived == False
            object.save()
        else:
            super().delete(request, *args, **kwargs)

        return JsonResponse({"id": object.pk})
