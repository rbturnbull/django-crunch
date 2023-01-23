from operator import mod
from typing import List
import re
from typing import Type
from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.utils.text import slugify
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.db.models import OuterRef, Subquery
from mptt.models import MPTTModel, TreeForeignKey
import humanize
from polymorphic.models import PolymorphicModel
from django_extensions.db.models import TimeStampedModel
from next_prev import next_in_order, prev_in_order
from polymorphic_tree.models import PolymorphicMPTTModel, PolymorphicTreeForeignKey


from . import enums, storages

User = get_user_model()


def OptionalCharField(max_length=255, default="", blank=True, **kwargs):
    return models.CharField(
        max_length=max_length, default=default, blank=blank, **kwargs
    )


class NextPrevMixin(models.Model):
    class Meta:
        abstract = True

    def next_in_order(self, **kwargs):
        return next_in_order(self, **kwargs)

    def prev_in_order(self, **kwargs):
        return prev_in_order(self, **kwargs)

    def get_admin_url(self):
        return reverse(
            f"admin:{self._meta.app_label}_{self._meta.model_name}_change",
            args=(self.pk,),
        )


class Item(NextPrevMixin, TimeStampedModel, PolymorphicMPTTModel):
    """
    A general class of object which can be placed in a hierachical tree. 

    Each item can be viewed online with a details page and each item can be given any number of attributes to store metadata.
    """
    parent = PolymorphicTreeForeignKey(
        "self",
        blank=True,
        null=True,
        default=None,
        related_name="children",
        on_delete=models.SET_DEFAULT,
    )
    name = models.CharField(max_length=1023, unique=True)
    description = models.CharField(
        max_length=1023,
        default="",
        blank=True,
        help_text="A short description in a sentence or more of this item.",
    )
    details = models.TextField(
        default="",
        blank=True,
        help_text="A detailed description of this item (written in Markdown).",
    )
    slug = AutoSlugField(populate_from="name", unique=True, max_length=255)
    # TODO Add tags

    def slugify_function(self, content):
        slug = slugify(content)
        if self.parent:
            return f"{self.parent.slug}:{slug}"
        return slug

    class Meta(PolymorphicMPTTModel.Meta):
        unique_together = ("parent", "slug")
        ordering = ('created', 'pk')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("crunch:item-detail", kwargs={"slug": self.slug})

    def items(self):
        return self.get_children()

    def descendant_attributes(
        self, attribute_type: Type = None, include_self: bool = True
    ) -> models.QuerySet:
        """Returns a queryset with all the attributes of the descendants of this item.

        Args:
            attribute_type (Type, optional): The type of the attribute to filter for. If `None` then it uses the `Attribute` class.
            include_self (bool, optional): Whether or not to include attributes of this item. Defaults to True.

        Returns:
            models.QuerySet: A queryset of attributes of items descended from this item.
        """
        attribute_type = attribute_type or Attribute
        return attribute_type.objects.filter(
            item__in=self.get_descendants(include_self=include_self)
        )

    def descendant_total_filesize(self) -> int:
        """
        Sums all the filesize attributes for this item and its descendants.

        Returns:
            int: The total sum of the filesize attributes of this item and all its descendants. 
                If there are no filesize attributes then it returns None.
        """
        
        filesize_attributes = self.descendant_attributes(
            attribute_type=FilesizeAttribute, include_self=True
        )

        if not filesize_attributes:
            return None

        return filesize_attributes.aggregate(models.Sum("value"))["value__sum"]

    def descendant_total_filesize_readable(self) -> str:
        """
        Sums all the filesize attributes for this item and its descendants and converts it to a human readable string.

        Returns:
            str: The total sum of the filesize attributes of this item and all its descendants in a human readable string. 
                If there are no filesize attributes then it returns 'None'.
        """
        descendant_total_filesize = self.descendant_total_filesize()

        if descendant_total_filesize:
            return humanize.naturalsize(descendant_total_filesize)

        return "None"

    def map(self):
        from .mapping import item_map

        return item_map(self)

    def descendant_latlongattributes(self):
        return self.descendant_attributes(
            attribute_type=LatLongAttribute, include_self=True
        )

    def has_descendant_latlongattributes(self):
        return self.descendant_latlongattributes().count() > 0

    def reslugify_descendants(self):
        for item in self.get_descendants(include_self=True):
            item.slug = item.slugify_function(item.name)
            item.save()


class Project(Item):
    """ 
    An item which collects a number of datasets which should be run with the same workflow. 

    Projects ought not to have parents in the tree structure of items.
    """
    workflow = models.TextField(
        default="",
        blank=True,
        help_text="URL to snakemake repository/shell script or its content.",
    )
    # More workflow languages need to be supported.
    # TODO assert parent is none

    def get_absolute_url(self):
        return reverse("crunch:project-detail", kwargs={"slug": self.slug})

    def unprocessed_datasets(self) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets in this project that are not complete and are not locked.
        """
        return Dataset.unprocessed().filter(id__in=self.items())

    def completed_datasets(self) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets in this project that are completed.
        """
        return Dataset.completed().filter(id__in=self.items())

    def running_datasets(self) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets in this project that are running.
        """
        return Dataset.running().filter(id__in=self.items())

    def failed_datasets(self) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets in this project that have failed.
        """
        return Dataset.failed().filter(id__in=self.items())

    def next_unprocessed_dataset(self) -> "Dataset":
        return self.unprocessed_datasets().first()


class Dataset(Item):
    """ 
    An item should be run once in a workflow.

    The parent of a dataset should be its project.
    """
    base_file_path = models.CharField(max_length=4096, default="", blank=True)
    locked = models.BooleanField(
        default=False,
        help_text="If the dataset is locked then it will not show up in the loop of available datasets.",
    )

    def save(self, *args, **kwargs):
        assert isinstance(self.parent, Project)

        if not self.base_file_path:
            self.base_file_path = storages.default_dataset_path(self.parent.slug, self.slug)
        return super().save(*args, **kwargs)

    def get_absolute_url(self) -> str:
        return f"{self.parent.get_absolute_url()}datasets/{self.slug}"

    @classmethod
    def completed_ids(cls) -> List[int]:
        """
        Returns a list of ids of all datasets which have a status with stage UPLOAD and state SUCCESS.
        """
        return Status.completed().values_list("dataset__id", flat=True)

    @classmethod
    def completed(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets which have a status with stage UPLOAD and state SUCCESS.
        """
        return cls.objects.filter(id__in=cls.completed_ids())

    @classmethod
    def incomplete(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets that are not complete (including unprocessed, running and failed datasets).
        """
        return cls.objects.exclude(id__in=cls.completed_ids())

    @classmethod
    def unprocessed(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all incomplete datasets that are not locked.
        """
        return cls.incomplete().filter(locked=False)

    @classmethod
    def inprocess(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all incomplete datasets that are locked (including running and failed datasets).
        """
        return cls.incomplete().filter(locked=True)

    @classmethod
    def has_status(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all datasets with at least one status.
        """
        statuses = Status.objects.filter(dataset=OuterRef("pk"))
        return cls.objects.filter(models.Exists(statuses))

    @classmethod
    def failed(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all incomplete unlocked datasets where the latest status has a state of 'FAILED'.
        """
        newest_statuses = Status.objects.filter(dataset=OuterRef("pk")).order_by(
            "-created"
        )
        annotated = cls.inprocess().annotate(
            newest_status_state=Subquery(newest_statuses.values("state")[:1])
        )
        return annotated.filter(newest_status_state=enums.State.FAIL)

    @classmethod
    def running(cls) -> models.QuerySet:
        """
        Returns a QuerySet of all incomplete unlocked datasets where the latest status does not have a state of 'FAILED'.
        """
        return cls.inprocess().exclude(id__in=cls.failed())

    @classmethod
    def next_unprocessed(cls) -> "Dataset":
        return cls.unprocessed().first()

    def files(self):
        return storages.storage_walk(self.base_file_path)


class Status(NextPrevMixin, TimeStampedModel):
    dataset = models.ForeignKey(
        Dataset, on_delete=models.CASCADE, related_name="statuses"
    )
    site_user = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, default=None, blank=True, null=True
    )
    stage = models.IntegerField(choices=enums.Stage.choices)
    state = models.IntegerField(choices=enums.State.choices)
    note = models.TextField(default="", blank=True)
    # Diagnostic info
    agent_user = OptionalCharField(
        help_text="The name of the user running the agent (see https://docs.python.org/3/library/getpass.html)."
    )
    version = OptionalCharField(
        help_text="The django-crunch version number of the agent."
    )
    revision = OptionalCharField(
        help_text="The django-crunch git revision hash of the agent."
    )
    # terminal = OptionalCharField(help_text="the tty or pseudo-tty associated with the agent user (see https://psutil.readthedocs.io/en/latest/).")
    system = OptionalCharField(
        help_text="Returns the system/OS name, such as 'Linux', 'Darwin', 'Java', 'Windows' (see https://docs.python.org/3/library/platform.html)."
    )
    system_release = OptionalCharField(
        help_text="Returns the system’s release, e.g. '2.2.0' or 'NT' (see https://docs.python.org/3/library/platform.html)."
    )
    system_version = OptionalCharField(
        help_text="Returns the system’s release version, e.g. '#3 on degas' (see https://docs.python.org/3/library/platform.html)."
    )
    machine = OptionalCharField(
        help_text="Returns the machine type, e.g. 'i386' (see https://docs.python.org/3/library/platform.html)."
    )
    hostname = OptionalCharField(
        help_text="The hostname of the machine where the agent was running (see https://docs.python.org/3/library/socket.html)."
    )
    ip_address = OptionalCharField(
        help_text="The hostname in IPv4 address format (see https://docs.python.org/3/library/socket.html)."
    )
    mac_address = OptionalCharField(
        help_text="The hardware address  (see https://docs.python.org/3/library/uuid.html)."
    )
    memory_total = models.BigIntegerField(
        default=None,
        blank=True,
        null=True,
        help_text="See https://psutil.readthedocs.io/en/latest/",
    )
    memory_free = models.BigIntegerField(
        default=None,
        blank=True,
        null=True,
        help_text="See https://psutil.readthedocs.io/en/latest/",
    )
    disk_total = models.BigIntegerField(
        default=None,
        blank=True,
        null=True,
        help_text="See https://psutil.readthedocs.io/en/latest/",
    )
    disk_free = models.BigIntegerField(
        default=None,
        blank=True,
        null=True,
        help_text="See https://psutil.readthedocs.io/en/latest/",
    )

    class Meta:
        verbose_name_plural = "statuses"

    def __str__(self):
        return f"{self.dataset}: {self.get_stage_display()} {self.get_state_display()}"

    def save(self, *args, **kwargs):

        # Lock dataset if necessary
        assert isinstance(self.dataset, Dataset)
        if not self.dataset.locked:
            self.dataset.locked = True
            self.dataset.save()

        super().save(*args, **kwargs)

    @classmethod
    def completed(cls):
        return Status.objects.filter(
            stage=enums.Stage.UPLOAD, state=enums.State.SUCCESS
        )


class Attribute(NextPrevMixin, TimeStampedModel, PolymorphicModel):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="attributes")
    key = models.CharField(max_length=255)

    def value_dict(self):
        return dict(key=self.key)

    def value_str(self):
        raise NotImplementedError("value_str not implemented for this attribute class")

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
            class_name = class_name[: -len("Attribute")]

        return re.sub(r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))", r" \1", class_name)


class ValueAttribute(Attribute):
    # Child classes need to give a 'value' field.

    class Meta:
        abstract = True

    def value_dict(self):
        d = super().value_dict()
        d["value"] = self.value
        return d

    def value_str(self):
        return self.value


class CharAttribute(ValueAttribute):
    """ An attribute for storing metadata as a string (of maximum length 1023 characters). """
    value = models.CharField(max_length=1023)


class FloatAttribute(ValueAttribute):
    value = models.FloatField()


class IntegerAttribute(ValueAttribute):
    value = models.IntegerField()


class FilesizeAttribute(ValueAttribute):
    value = models.PositiveBigIntegerField(
        help_text="The filesize of this item in bytes."
    )

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
    """ An attribute for storing a geolocation (in decimal degrees). """
    latitude = models.DecimalField(
        max_digits=12,
        decimal_places=9,
        help_text="The latitude of this location in decimal degrees.",
    )
    longitude = models.DecimalField(
        max_digits=12,
        decimal_places=9,
        help_text="The longitude of this location in decimal degrees.",
    )

    def value_dict(self):
        d = super().value_dict()
        d["latitude"] = self.latitude
        d["longitude"] = self.longitude
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
