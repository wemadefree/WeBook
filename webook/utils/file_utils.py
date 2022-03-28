import os

def get_extension(filename: str) -> str:
    """ 
    Get the extension from the given filename

    :param filename: The filename to extract extension from
    :type filename: str

    :return: The extension of filename, for instance '.jpg'
    :rtype: str
    """
    return os.path.splitext(filename[1])
