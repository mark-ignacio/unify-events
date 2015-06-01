from django.template.defaultfilters import slugify

import events.models


def generate_unique_slug(title, clazz, unique):
    """
    Generate a unique slug for the given class.

    Args:
      title  (str): The title of the tag.
      clazz  (obj): The tag model object.
      unique (bool): Whether or not the slug is "unique".

    Returns:
      str: The unique slug title (e.g., "joe-is-a-slug").
    """
    slug = slugify(title)

    if unique:
        slug_cnt = 0
        orig_slug = slug
        is_unique_slug = False
        while not is_unique_slug:
            try:
                clazz.objects.get(slug=slug)
                # Slug is not unique so try the next one
                slug_cnt += 1
                slug = orig_slug + '-' + str(slug_cnt)
            except clazz.DoesNotExist:
                # No object exists with this slug so use it!
                is_unique_slug = True
    return slug


def pre_save_slug(sender, **kwargs):
    """
    Generate a slug before the object is saved.

    Args:
      sender (obj): The model object to pre-save.
      **kwargs: Arbitrary keyword arguments.
    """
    instance = kwargs['instance']
    instance.slug = generate_unique_slug(instance.title, sender, False)


def pre_save_unique_slug(sender, **kwargs):
    """
    Generate a slug before the object is saved.

    Args:
      sender (obj): The unique model object to pre-save.
      **kwargs: Arbitrary keyword arguments.
    """
    instance = kwargs['instance']
    instance.slug = generate_unique_slug(instance.title, sender, True)


def format_to_mimetype(format):
    """Provides a mapping between frontend document formats and mimetypes to be
    returned with the resulting response.

    Args:
      format (str): The format type of the response.

    Returns:
      str: The appropriate mimetype, otherwise "text/html".
    """
    return {
        'json': 'application/json',
        'rss': 'application/rss+xml',
        'html': 'text/html',
        'xml': 'text/xml',
        'ics': 'text/calendar',
    }.get(format, 'text/html')
