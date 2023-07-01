from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Неважное'
    NOTE_TEXT = 'Много слов о важном.'
    NOTE_SLUG = 'text_day'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Rabbit')
        cls.author_client = Client()
        cls.add_note_url = reverse('notes:add')
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(
            self.add_note_url, data=self.form_data
        )
        login_url = reverse('users:login')
        self.assertRedirects(
            self.client.post(
                self.add_note_url, data=self.form_data
            ), f'{login_url}?next={self.add_note_url}'
        )
        self.assertEqual(
            Note.objects.count(), 0
        )

    def test_author_can_create_note(self):
        self.author_client.force_login(self.author)
        self.assertRedirects(
            self.author_client.post(
                self.add_note_url, data=self.form_data
            ), reverse('notes:success')
        )
        self.assertEqual(
            Note.objects.count(), 1
        )
        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.slug, self.NOTE_SLUG)
        self.assertEqual(note.author, self.author)


class TestNotePage(TestCase):
    NOTE_TITLE = 'Важное'
    NOTE_TEXT = 'Много слов о важном.'
    NOTE_SLUG = 'text_day'
    NOTE_NEW_TEXT = 'Много слов от неважном'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Pink Rabbit')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author,
            )
        cls.reader = User.objects.create(username='White Rabbit')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_NEW_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        self.assertRedirects(
            self.author_client.delete(self.delete_url), self.success_url
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(
            response.status_code, HTTPStatus.NOT_FOUND
        )
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        self.assertRedirects(
            self.author_client.post(
                self.edit_url, data=self.form_data
            ), self.success_url
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_NEW_TEXT)
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_not_unique_slug(self):
        self.form_data['slug'] = self.note.slug
        self.assertFormError(
            self.author_client.post(
                reverse('notes:add'), data=self.form_data
            ), 'form', 'slug', errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), 1)


class TestSlugField(TestCase):
    NOTE_TITLE = 'Важное'
    NOTE_TEXT = 'Много слов о важном.'
    NOTE_SLUG = 'text_day'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Pink Rabbit')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.success_url = reverse('notes:success')
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.NOTE_SLUG,
        }

    def test_empty_slug(self):
        self.add_url = reverse('notes:add')
        self.form_data.pop('slug')
        self.assertRedirects(
            self.author_client.post(
                self.add_url, data=self.form_data
            ), self.success_url
        )
        self.new_note = Note.objects.get()
        self.assertEqual(
            self.new_note.slug, slugify(self.form_data['title'])
        )
