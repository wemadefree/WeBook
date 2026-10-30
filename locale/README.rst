Translations
============

English is the canonical source language for user-facing text. Templates and
Python code should use English message IDs and wrap every visible string in
``{% trans %}``, ``{% blocktrans %}``, ``gettext()`` or ``gettext_lazy()``.
Norwegian belongs in the ``nb`` catalog; do not use Norwegian text as a
message ID and do not hard-code it in templates or JavaScript configuration.

Update the catalogs from the repository root with::

    python manage.py makemessages -l nb
    python manage.py compilemessages

Compile messages before testing Norwegian. The generated ``django.mo`` files
are build artifacts and should not be edited by hand.
