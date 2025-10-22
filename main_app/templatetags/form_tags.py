# main_app/templatetags/form_tags.py

from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_classes):
    """
    Safely append CSS classes to a Django BoundField's widget.
    Preserves existing widget attrs and merges classes.
    """
    attrs = getattr(field.field.widget, 'attrs', {}).copy()
    existing = attrs.get('class', '')
    merged = f"{existing} {css_classes}".strip()
    attrs['class'] = merged
    return field.as_widget(attrs=attrs)