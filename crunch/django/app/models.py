from django.db import models
from django_extensions.db.fields import AutoSlugField
from django.urls import reverse
from django.contrib.auth import get_user_model
User = get_user_model()

from polymorphic.models import PolymorphicModel
from django_extensions.db.models import TimeStampedModel

from . import enums

def OptionalCharField(max_length=255, default="", blank=True, **kwargs):
    return models.CharField(max_length=max_length, default=default, blank=blank, **kwargs)


class Project(TimeStampedModel, PolymorphicModel):
    name = models.CharField(max_length=1023, unique=True)
    description = models.CharField(max_length=1023, default="", blank=True, help_text="A short description in a sentence or more of this project.")
    details = models.TextField(default="", blank=True, help_text="A detailed description of this project (written in Markdown).")    
    slug = AutoSlugField(populate_from='name', unique=True)
    snakefile = models.TextField(default="", blank=True)
    # TODO Add tags

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("crunch:project-detail", kwargs={"slug": self.slug})


class Dataset(TimeStampedModel, PolymorphicModel):
    name = models.CharField(max_length=1023)
    description = models.CharField(max_length=1023, default="", blank=True, help_text="A short description in a sentence or more of this dataset.")
    details = models.TextField(default="", blank=True, help_text="A detailed description of this dataset (written in Markdown).")
    slug = AutoSlugField(populate_from='name')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="datasets")
    # TODO Add tags
    # TODO consolidate with Project stuff because much is repeated


    def __str__(self):
        return self.name

    class Meta:
        unique_together = ('project', 'name',)

    def get_absolute_url(self):
        return f"{self.project.get_absolute_url()}datasets/{self.slug}"

    @classmethod
    def unprocessed(cls):
        return cls.objects.filter(statuses=None)

    @classmethod
    def next_unprocessed(cls):
        return cls.unprocessed().first()


class Status(TimeStampedModel):
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


class Attribute(TimeStampedModel, PolymorphicModel):
    # project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name='attributes')
    key = models.CharField(max_length=255)

    def value_dict(self):
        return dict(key=self.key)

    def value_str(self):
        return ""

    def value_html(self):
        return self.value_str()

    def __str__(self):
        return f"{self.key}: {self.value_str()}"


class CharAttribute(Attribute):
    value = models.CharField(max_length=1023)
    
    def value_dict(self):
        d = super().value_dict()
        d['value'] = self.value
        return d

    def value_str(self):
        return self.value


class FloatAttribute(Attribute):
    value = models.FloatField()

    def value_dict(self):
        d = super().value_dict()
        d['value'] = self.value
        return d

    def value_str(self):
        return f"{self.value}"


class IntegerAttribute(Attribute):
    value = models.IntegerField()

    def value_dict(self):
        d = super().value_dict()
        d['value'] = self.value
        return d

    def value_str(self):
        return f"{self.value}"


