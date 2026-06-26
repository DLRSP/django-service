from django.http import Http404
from django.utils.functional import cached_property
from django.views.generic import ListView, DetailView
from filer_optimizer.utils import annotate_queryset_with_thumbnails
from .models import ServiceCategory, Service, ServiceImage
from django.conf import settings
from django.db.models import Q


def get_prev_obj(current_obj_pk, **kwargs):
    return (
        Service.objects.filter(published=True)
        .filter(pk__lt=current_obj_pk)
        .values("category__slug", "name", "slug")
        .order_by("-order")
        .first()
    )


def get_next_obj(current_recipe_pk, **kwargs):
    return (
        Service.objects.filter(published=True)
        .filter(pk__gt=current_recipe_pk)
        .values("category__slug", "name", "slug")
        .order_by("order")
        .first()
    )


class ServiceCategoryListView(ListView):
    """
    Service's Categories List
    """

    model = ServiceCategory


class ServiceCategoryDetailView(DetailView):
    """
    Service's Category Detail
    """

    model = ServiceCategory
    ordering = ["order"]
    # template_name = "recipes/recipe_list_image_grid.html"

    def get_object(self, **kwargs):
        queryset = ServiceCategory.objects.filter(slug=self.kwargs["slug_cat"]).values(
            "slug", "name", "description"
        )
        queryset = annotate_queryset_with_thumbnails(
            queryset, "head", img_name="image_header"
        )
        return queryset[0]

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        queryset = Service.objects.filter(category__slug=context["object"]["slug"]).values(
            "category__slug", "category__name", "slug", "name"
        )
        queryset = annotate_queryset_with_thumbnails(
            queryset, "head", img_name="image_preview"
        )
        context["object_list"] = queryset
        return context


class ServiceListView(ListView):
    """
    Services List
    """

    model = Service
    ordering = ["category__order", "order"]

    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        return context


class ServiceDetailView(DetailView):
    """
    Service Detail
    """

    model = Service

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.query = None
        self.query_img = None

    def create_query(self, field="slug"):
        languages = dict(settings.LANGUAGES).keys()
        query = Q()
        for lang in languages:
            # modeltranslation builds field names with underscores, so a language
            # code such as "zh-hans" maps to the "<field>_zh_hans" column.
            kwargs = {f"{field}_{lang.replace('-', '_')}": self.kwargs["slug"]}
            query |= Q(**kwargs)
        return query

    def get_object(self, **kwargs):
        self.query = self.create_query("slug")
        self.query_img = self.create_query("obj__slug")

        queryset = Service.objects.filter(self.query)
        if queryset.exists():
            queryset = annotate_queryset_with_thumbnails(queryset, "head", "image_header")
            queryset = annotate_queryset_with_thumbnails(queryset, "preview", "image_preview", "thumbnail_preview")
            return queryset.get()
        else:
            raise Http404

    @cached_property
    def get_object_images(self):
        images_list = []
        queryset = ServiceImage.objects.filter(self.query_img).order_by("-highlighted").distinct()
        if queryset.exists():
            queryset = annotate_queryset_with_thumbnails(queryset, "head")
        for image in queryset:
            images_list.append(image)
        return images_list

    @cached_property
    def get_tag_list(self):
        return list(self.object.tags.all())

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context['prev_obj'] = get_prev_obj(context['object'].pk)
        context['next_obj'] = get_next_obj(context['object'].pk)
        context['images_list'] = self.get_object_images
        context['tags_list'] = self.get_tag_list
        return context
