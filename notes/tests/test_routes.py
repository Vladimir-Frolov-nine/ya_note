from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):
    TITLE = 'Утро субботы.'
    SLUG = 'note'
    USERNAME = 'Rabbit'
    TEXT = 'Интересное утро.'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username=cls.USERNAME)
        cls.reader = User.objects.create(username='Reader')
        cls.note = Note.objects.create(
            author=cls.author,
            title=cls.TITLE,
            text=cls.TEXT,
            slug=cls.SLUG,
        )

    def test_page_availability_for_anonymous(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for name, args in urls:
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_availability_for_auth_user(self):
        urls = (
            'notes:list', 'notes:add', 'notes:success',
        )
        for name in urls:
            with self.subTest(name=name):
                self.client.force_login(self.reader)
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_availability_for_author(self):
        urls = (
            'notes:detail', 'notes:edit', 'notes:delete',
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                self.client.force_login(self.author)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_edit_and_delete(self):
        urls = (
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, args in urls:
                with self.subTest(name=name, args=args):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous(self):
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        login_url = reverse('users:login')
        for name, args in urls:
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
