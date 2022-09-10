from classytags.helpers import InclusionTag
from classytags.arguments import Argument
from classytags.core import Options
from django import template

register = template.Library()


class ItemMapTag(InclusionTag):
    name = "item_map"
    template = "crunch/item_map.html"
    options = Options(
        Argument("item"),
    )

    def get_context(self, context, item):
        return {"item": item}


register.tag(ItemMapTag)


class DatasetListTag(InclusionTag):
    name = "dataset_list"
    template = "crunch/dataset_list.html"
    options = Options(
        Argument("datasets"),
    )

    def get_context(self, context, datasets):
        return {"datasets": datasets}


register.tag(DatasetListTag)
