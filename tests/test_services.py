"""Unit tests for the django-service module."""

import base64
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from filer.models import Image as FilerImage
from hashtag.models import MyTagGroup

from services import context_processors
from services.models import Service, ServiceCategory, ServiceImage
from services.sitemaps import ServiceCategorySitemap, ServiceSitemap
from services.views import (
    ServiceCategoryDetailView,
    ServiceDetailView,
    ServiceListView,
    get_next_obj,
    get_prev_obj,
)

# Smallest possible valid 1x1 PNG.
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk"
    "+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


class BaseFixtureMixin:
    """Shared helpers to build the model graph used across tests."""

    @classmethod
    def make_user(cls):
        return get_user_model().objects.create_user(
            username="author", password="pwd"
        )

    @classmethod
    def make_image(cls, user, filename="pic.png"):
        return FilerImage.objects.create(
            owner=user,
            original_filename=filename,
            file=ContentFile(PNG_1PX, name=filename),
        )

    @classmethod
    def make_category(cls, user, name="Cat", slug="cat", published=True):
        return ServiceCategory.objects.create(
            name=name, slug=slug, created_by=user, published=published
        )

    @classmethod
    def make_service(cls, user, category, name="Svc", slug="svc", published=True):
        return Service.objects.create(
            name=name,
            slug=slug,
            category=category,
            created_by=user,
            published=published,
        )


class ModelStrTests(BaseFixtureMixin, TestCase):
    """__str__ representations."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.service = cls.make_service(cls.user, cls.category)
        cls.image = cls.make_image(cls.user)
        cls.service_image = ServiceImage.objects.create(
            image=cls.image, obj=cls.service
        )

    def test_category_str(self):
        self.assertEqual(str(self.category), "Cat")

    def test_service_str(self):
        self.assertEqual(str(self.service), "Svc")

    def test_service_image_str(self):
        self.assertEqual(str(self.service_image), "pic.png")


class SitemapTests(BaseFixtureMixin, TestCase):
    """Sitemap items() and location() use the correct URL names."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.service = cls.make_service(cls.user, cls.category)

    def test_category_sitemap(self):
        sitemap = ServiceCategorySitemap()
        self.assertIn(self.category, list(sitemap.items()))
        self.assertEqual(
            sitemap.location(self.category),
            reverse("services-category-detail", args=[self.category.slug]),
        )

    def test_service_sitemap(self):
        sitemap = ServiceSitemap()
        self.assertIn(self.service, list(sitemap.items()))
        self.assertEqual(
            sitemap.location(self.service),
            reverse(
                "service-detail",
                args=[self.service.category.slug, self.service.slug],
            ),
        )


class NavigationHelperTests(BaseFixtureMixin, TestCase):
    """get_prev_obj / get_next_obj navigation helpers."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.first = cls.make_service(cls.user, cls.category, name="A", slug="a")
        cls.second = cls.make_service(cls.user, cls.category, name="B", slug="b")
        cls.third = cls.make_service(cls.user, cls.category, name="C", slug="c")

    def test_get_prev_obj(self):
        prev = get_prev_obj(self.second.pk)
        self.assertEqual(prev["slug"], "a")

    def test_get_prev_obj_none(self):
        self.assertIsNone(get_prev_obj(self.first.pk))

    def test_get_next_obj(self):
        nxt = get_next_obj(self.second.pk)
        self.assertEqual(nxt["slug"], "c")

    def test_get_next_obj_none(self):
        self.assertIsNone(get_next_obj(self.third.pk))


class ContextProcessorTests(BaseFixtureMixin, TestCase):
    """common_context cache hit/miss and error branches."""

    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()
        self.user = self.make_user()
        self.category = self.make_category(self.user)
        self.make_service(self.user, self.category)

    def _request(self):
        request = self.factory.get("/")
        setattr(request, "session", {})
        setattr(request, "_messages", FallbackStorage(request))
        return request

    def test_cache_miss_builds_context(self):
        context = context_processors.common_context(self._request())
        self.assertIn("all_category", context)
        self.assertIn("all_service", context)

    def test_cache_hit_returns_cached(self):
        request = self._request()
        context_processors.common_context(request)
        cached = context_processors.common_context(request)
        self.assertIn("all_category", cached)

    def test_cache_get_failure_falls_back_to_build(self):
        with mock.patch.object(
            context_processors.cache, "get", side_effect=Exception("down")
        ):
            context = context_processors.common_context(self._request())
        self.assertIn("all_service", context)

    def test_build_failure_records_message(self):
        request = self._request()
        with mock.patch.object(
            context_processors,
            "annotate_queryset_with_thumbnails",
            side_effect=Exception("boom"),
        ):
            result = context_processors.common_context(request)
        self.assertIsNone(result)
        self.assertEqual(len(list(get_messages(request))), 1)


class ServiceCategoryDetailViewTests(BaseFixtureMixin, TestCase):
    """ServiceCategoryDetailView get_object / get_context_data."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.service = cls.make_service(cls.user, cls.category)

    def _view(self):
        view = ServiceCategoryDetailView()
        request = RequestFactory().get("/")
        view.setup(request, slug_cat=self.category.slug)
        return view

    def test_get_object_returns_values_dict(self):
        view = self._view()
        obj = view.get_object()
        self.assertEqual(obj["slug"], self.category.slug)

    def test_get_context_data_includes_services(self):
        view = self._view()
        view.object = view.get_object()
        context = view.get_context_data(object=view.object)
        slugs = [row["slug"] for row in context["object_list"]]
        self.assertIn(self.service.slug, slugs)


class ServiceListViewTests(BaseFixtureMixin, TestCase):
    """ServiceListView get_context_data."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.make_service(cls.user, cls.category)

    def test_get_context_data(self):
        view = ServiceListView()
        request = RequestFactory().get("/")
        view.setup(request)
        view.object_list = view.get_queryset()
        context = view.get_context_data()
        self.assertIn("object_list", context)


class ServiceDetailViewTests(BaseFixtureMixin, TestCase):
    """ServiceDetailView object resolution, images, tags and context."""

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.make_user()
        cls.category = cls.make_category(cls.user)
        cls.service = cls.make_service(cls.user, cls.category, name="Svc", slug="svc")
        # hashtag.MyTag.group defaults to FK id=1, so a default group must exist.
        MyTagGroup.objects.create(name="Default", slug="default")
        cls.service.tags.add("alpha", "beta")
        cls.image = cls.make_image(cls.user)
        cls.service_image = ServiceImage.objects.create(
            image=cls.image, obj=cls.service
        )

    def _view(self, slug):
        view = ServiceDetailView()
        request = RequestFactory().get("/")
        view.setup(request, slug_cat=self.category.slug, slug=slug)
        return view

    def test_create_query_covers_all_languages(self):
        view = self._view("svc")
        query = view.create_query("slug")
        # one Q child per configured language
        self.assertTrue(len(query.children) >= 10)

    def test_get_object_found(self):
        view = self._view("svc")
        obj = view.get_object()
        self.assertEqual(obj.pk, self.service.pk)

    def test_get_object_missing_raises_404(self):
        view = self._view("does-not-exist")
        with self.assertRaises(Http404):
            view.get_object()

    def test_get_object_images(self):
        view = self._view("svc")
        view.object = view.get_object()
        images = view.get_object_images
        self.assertEqual(images, [self.service_image])

    def test_get_object_images_empty(self):
        empty = self.make_service(
            self.user, self.category, name="Empty", slug="empty"
        )
        view = self._view("empty")
        view.object = view.get_object()
        self.assertEqual(view.get_object_images, [])
        self.assertEqual(empty.slug, "empty")

    def test_get_tag_list(self):
        view = self._view("svc")
        view.object = view.get_object()
        tag_names = sorted(tag.name for tag in view.get_tag_list)
        self.assertEqual(tag_names, ["alpha", "beta"])

    def test_get_context_data(self):
        view = self._view("svc")
        view.object = view.get_object()
        context = view.get_context_data(object=view.object)
        self.assertIn("prev_obj", context)
        self.assertIn("next_obj", context)
        self.assertEqual(context["images_list"], [self.service_image])
        self.assertEqual(len(context["tags_list"]), 2)
