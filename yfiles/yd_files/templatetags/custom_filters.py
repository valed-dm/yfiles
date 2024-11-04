from django import template

from yfiles.yd_files.utils.convert_bytes import convert_bytes

register = template.Library()
register.filter("convert_bytes", convert_bytes)
