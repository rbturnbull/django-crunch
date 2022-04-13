from operator import mod
import re
from typing import Type
from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from mptt.models import MPTTModel, TreeForeignKey
import humanize
from polymorphic.models import PolymorphicModel
from django_extensions.db.models import TimeStampedModel
from next_prev import next_in_order, prev_in_order
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey

from . import enums, storages

User = get_user_model()

def OptionalCharField(max_length=255, default="", blank=True, **kwargs):
    return models.CharField(max_length=max_length, default=default, blank=blank, **kwargs)


class NextPrevMixin(models.Model):
    class Meta:
        abstract = True

    def next_in_order(self, **kwargs):
        return next_in_order( self )

    def prev_in_order(self, **kwargs):
        return prev_in_order( self )

    def get_admin_url(self):
        return reverse(f'admin:{self._meta.app_label}_{self._meta.model_name}_change', args=(self.pk,))


class Item(NextPrevMixin, TimeStampedModel, PolymorphicMPTTModel):
    parent = PolymorphicTreeForeignKey('self', blank=True, null=True, default=None, related_name='children', on_delete=models.SET_DEFAULT)
    name = models.CharField(max_length=1023, unique=True)
    description = models.CharField(max_length=1023, default="", blank=True, help_text="A short description in a sentence or more of this item.")
    details = models.TextField(default="", blank=True, help_text="A detailed description of this item (written in Markdown).")    
    slug = AutoSlugField(populate_from='name', unique=True, max_length=255)
    # TODO Add tags

    def slugify_function(self, content):
        slug = slugify(content)
        if self.parent:
            return f"{self.parent.slug}.{slug}"
        return slug

    class Meta(PolymorphicMPTTModel.Meta):
        unique_together = ('parent', 'slug')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("crunch:item-detail", kwargs={"slug": self.slug})

    def items(self):
        return self.get_children()

    def descendant_attributes(self, attribute_type:Type=None, include_self:bool=True) -> models.QuerySet:
        """Returns a queryset with all the attributes of the descendants of this item.

        Args:
            attribute_type (Type, optional): The type of the attribute to filter for. If `None` then it uses the `Attribute` class.
            include_self (bool, optional): Whether or not to include attributes of this item. Defaults to True.

        Returns:
            models.QuerySet: A queryset of attributes of items descended from this item.
        """
        attribute_type = attribute_type or Attribute
        return attribute_type.objects.filter(item__in=self.get_descendants(include_self=include_self))

    def descendant_total_filesize(self):
        filesize_attributes = self.descendant_attributes(attribute_type=FilesizeAttribute, include_self=True)

        if not filesize_attributes:
            return None

        return filesize_attributes.aggregate(models.Sum('value'))['value__sum']

    def descendant_total_filesize_readable(self) -> str:
        descendant_total_filesize = self.descendant_total_filesize()

        if descendant_total_filesize:
            return humanize.naturalsize(descendant_total_filesize)
        
        return "None"

    def map(self):
        from .mapping import item_map
        return item_map(self)

    def descendant_latlongattributes(self):
        return self.descendant_attributes(attribute_type=LatLongAttribute, include_self=True)

    def has_descendant_latlongattributes(self):
        return self.descendant_latlongattributes().count() > 0

class Project(Item):
    workflow = models.TextField(default="", blank=True, help_text="URL to snakemake repository or text of snakefile.")
    # More workflow languages need to be supported.
    
    def get_absolute_url(self):
        return reverse("crunch:project-detail", kwargs={"slug": self.slug})

    # TODO assert parent is none


class Dataset(Item):
    # TODO assert parent is Project

    def get_absolute_url(self):
        return f"{self.parent.get_absolute_url()}datasets/{self.slug}"

    @classmethod
    def unprocessed(cls):
        return cls.objects.filter(statuses=None)

    @classmethod
    def next_unprocessed(cls):
        return cls.unprocessed().first()

    def base_file_path(self):
        return storages.dataset_path( self.parent.slug, self.slug )

    def files(self):
        return storages.storage_walk(self.base_file_path())
        

class Status(NextPrevMixin, TimeStampedModel):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='statuses')
    site_user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=None, blank=True, null=True)
    stage = models.IntegerField(choices=enums.Stage.choices)
    state = models.IntegerField(choices=enums.State.choices)
    note = models.TextField(default="", blank=True)
    # Diagnostic info
    agent_user = OptionalCharField(help_text="The name of the user running the agent (see https://docs.python.org/3/library/getpass.html).")
    version = OptionalCharField(help_text="The django-crunch version number of the agent.")
    revision = OptionalCharField(help_text="The django-crunch git revision hash of the agent.")
    # terminal = OptionalCharField(help_text="the tty or pseudo-tty associated with the agent user (see https://psutil.readthedocs.io/en/latest/).")
    system = OptionalCharField(help_text="Returns the system/OS name, such as 'Linux', 'Darwin', 'Java', 'Windows' (see https://docs.python.org/3/library/platform.html).")
    system_release = OptionalCharField(help_text="Returns the system’s release, e.g. '2.2.0' or 'NT' (see https://docs.python.org/3/library/platform.html).")
    system_version = OptionalCharField(help_text="Returns the system’s release version, e.g. '#3 on degas' (see https://docs.python.org/3/library/platform.html).")
    machine = OptionalCharField(help_text="Returns the machine type, e.g. 'i386' (see https://docs.python.org/3/library/platform.html).")
    hostname = OptionalCharField(help_text="The hostname of the machine where the agent was running (see https://docs.python.org/3/library/socket.html).")
    ip_address = OptionalCharField(help_text="The hostname in IPv4 address format (see https://docs.python.org/3/library/socket.html).")
    mac_address = OptionalCharField(help_text="The hardware address  (see https://docs.python.org/3/library/uuid.html).")
    memory_total = models.PositiveIntegerField( default=None, blank=True, null=True, help_text="See https://psutil.readthedocs.io/en/latest/")
    memory_free = models.PositiveIntegerField( default=None, blank=True, null=True, help_text="See https://psutil.readthedocs.io/en/latest/")
    disk_total = models.PositiveIntegerField( default=None, blank=True, null=True, help_text="See https://psutil.readthedocs.io/en/latest/")
    disk_free = models.PositiveIntegerField( default=None, blank=True, null=True, help_text="See https://psutil.readthedocs.io/en/latest/")

    class Meta:
        verbose_name_plural = "statuses"

    def __str__(self):
        return f"{self.dataset}: {self.get_stage_display()} {self.get_state_display()}"


class Attribute(NextPrevMixin, TimeStampedModel, PolymorphicModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='attributes')
    key = models.CharField(max_length=255)

    def value_dict(self):
        return dict(key=self.key)

    def value_str(self):
        return ""

    def value_html(self):
        return self.value_str()

    def __str__(self):
        return f"{self.key}: {self.value_str()}"

    def type_str(self) -> str:
        """
        Returns a string describing this type of attribute.

        By default it returns the class name with spaces added where implied by camel case.

        Returns:
            str: The type of this attribute as a string.
        """
        class_name = self.__class__.__name__
        if class_name.endswith("Attribute"):
            class_name = class_name[:-len("Attribute")]
        
        return re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \1', class_name) 


class ValueAttribute(Attribute):
    # Child classes need to give a 'value' field.

    class Meta:
        abstract = True
    
    def value_dict(self):
        d = super().value_dict()
        d['value'] = self.value
        return d

    def value_str(self):
        return self.value


class CharAttribute(ValueAttribute):
    value = models.CharField(max_length=1023)
    

class FloatAttribute(ValueAttribute):
    value = models.FloatField()


class IntegerAttribute(ValueAttribute):
    value = models.IntegerField()


class FilesizeAttribute(ValueAttribute):
    value = models.PositiveBigIntegerField(help_text="The filesize of this item in bytes.")

    def value_str(self):
        return humanize.naturalsize(self.value)


class BooleanAttribute(ValueAttribute):
    value = models.BooleanField()


class DateTimeAttribute(ValueAttribute):
    value = models.DateTimeField()


class DateAttribute(ValueAttribute):
    value = models.DateField()


class URLAttribute(ValueAttribute):
    value = models.URLField(max_length=1023)
    
    def value_html(self):
        return format_html(
            "<a href='{}'>{}</a>",
            self.value,
            self.value,
        )


class LatLongAttribute(Attribute):
    latitude = models.DecimalField(max_digits=12, decimal_places=9, help_text="The latitude of this location in decimal degrees.")
    longitude = models.DecimalField(max_digits=12, decimal_places=9, help_text="The longitude of this location in decimal degrees.")
    
    def value_dict(self):
        d = super().value_dict()
        d['latitude'] = self.latitude
        d['longitude'] = self.longitude
        return d

    def value_str(self):
        return f"{self.latitude:+}{self.longitude:+}/"

    def value_html(self):
        return format_html(
            "<a href='https://www.google.com/maps/place/{},{}'>{}</a>",
            self.latitude,
            self.longitude,
            self.value_str(),
        )


