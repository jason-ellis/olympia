from django import http

import mock
from nose.tools import eq_

import amo.tests
from addons import decorators as dec
from addons.models import Addon


class TestAddonView(amo.tests.TestCase):

    def setUp(self):
        super(TestAddonView, self).setUp()
        self.addon = Addon.objects.create(slug='x', type=1)
        self.func = mock.Mock()
        self.func.return_value = mock.sentinel.OK
        self.func.__name__ = 'mock_function'
        self.view = dec.addon_view(self.func)
        self.request = mock.Mock()
        self.slug_path = '/addon/%s/reviews' % self.addon.slug
        self.request.path = self.id_path = '/addon/%s/reviews' % self.addon.id
        self.request.GET = {}

    def test_301_by_id(self):
        res = self.view(self.request, str(self.addon.id))
        self.assert3xx(res, self.slug_path, 301)

    def test_slug_replace_no_conflict(self):
        self.request.path = '/addon/{id}/reviews/{id}345/path'.format(
            id=self.addon.id)
        res = self.view(self.request, str(self.addon.id))
        self.assert3xx(res, '/addon/{slug}/reviews/{id}345/path'.format(
            id=self.addon.id, slug=self.addon.slug), 301)

    def test_301_with_querystring(self):
        self.request.GET = mock.Mock()
        self.request.GET.urlencode.return_value = 'q=1'
        res = self.view(self.request, str(self.addon.id))
        self.assert3xx(res, self.slug_path + '?q=1', 301)

    def test_200_by_slug(self):
        res = self.view(self.request, self.addon.slug)
        eq_(res, mock.sentinel.OK)

    def test_404_by_id(self):
        with self.assertRaises(http.Http404):
            self.view(self.request, str(self.addon.id * 2))

    def test_404_by_slug(self):
        with self.assertRaises(http.Http404):
            self.view(self.request, self.addon.slug + 'xx')

    def test_alternate_qs_301_by_id(self):
        def qs():
            return Addon.objects.filter(type=1)

        view = dec.addon_view_factory(qs=qs)(self.func)
        res = view(self.request, str(self.addon.id))
        self.assert3xx(res, self.slug_path, 301)

    def test_alternate_qs_200_by_slug(self):
        def qs():
            return Addon.objects.filter(type=1)

        view = dec.addon_view_factory(qs=qs)(self.func)
        res = view(self.request, self.addon.slug)
        eq_(res, mock.sentinel.OK)

    def test_alternate_qs_404_by_id(self):
        def qs():
            return Addon.objects.filter(type=2)

        view = dec.addon_view_factory(qs=qs)(self.func)
        with self.assertRaises(http.Http404):
            view(self.request, str(self.addon.id))

    def test_alternate_qs_404_by_slug(self):
        def qs():
            return Addon.objects.filter(type=2)

        view = dec.addon_view_factory(qs=qs)(self.func)
        with self.assertRaises(http.Http404):
            view(self.request, self.addon.slug)

    def test_addon_no_slug(self):
        app = Addon.objects.create(type=1, name='xxxx')
        res = self.view(self.request, app.slug)
        eq_(res, mock.sentinel.OK)

    def test_slug_isdigit(self):
        app = Addon.objects.create(type=1, name='xxxx')
        app.update(slug=str(app.id))
        r = self.view(self.request, app.slug)
        eq_(r, mock.sentinel.OK)
        request, addon = self.func.call_args[0]
        eq_(addon, app)
