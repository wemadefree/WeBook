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

    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


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
        return JsonResponse({'id': self.object.pk})