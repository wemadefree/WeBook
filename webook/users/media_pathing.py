from webook.utils import file_utils

def profile_picture_path (instance, filename):
    return f'users/{instance.id}/profile_picture{file_utils.get_extension(filename)}'
