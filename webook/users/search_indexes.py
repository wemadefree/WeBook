from haystack import indexes
from webook.users.models import User

class UserIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    email = indexes.CharField(model_attr='email')
    timezone = indexes.CharField(model_attr='timezone')
    is_user_admin = indexes.BooleanField(model_attr='is_user_admin')
    is_active = indexes.BooleanField(model_attr='is_active')
    role = indexes.CharField()

    def prepare_role(self, obj):
        """Same values as the role filter on the user list: "superuser", a group name, or "none" """
        if obj.is_superuser:
            return "superuser"
        group = obj.groups.first()
        return group.name if group else "none"


    def get_model(self):
        return User

    def index_queryset(self, using=None):
        return self.get_model().objects.all()