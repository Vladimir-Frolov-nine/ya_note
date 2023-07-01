from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestListPage(TestCase):
    PAGE = 10

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Rabbit')
        cls.reader = User.objects.create(username='Reader')
        cls.list_url = reverse('notes:list')
        cls.note = Note.objects.bulk_create(
            Note(
                title=f'Текст дня {index}.',
                text='Много слов.',
                slug=f'text_day{index}',
                author=cls.author
            )for index in range(cls.PAGE)
        )

    def test_notes_for_different_users(self):
        users = (
            (self.author, self.PAGE),
            (self.reader, 0),
        )
        for user, status in users:
            self.client.force_login(user)
            response = self.client.get(self.list_url)
            self.assertEqual(len(response.context['object_list']), status)


class TestContentNote(TestCase):
    NOTE_TITLE = 'Важное.'
    NOTE_TEXT = 'Много слов о важном.'
    NOTE_SLUG = 'important_text'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Rabbit')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author
        )

    def test_content_note_appears_on_page_before_being_deleted(self):
        self.delete_url = reverse('notes:delete', args=(self.note.slug,))
        response = self.author_client.get(self.delete_url)
        self.assertIn('note', response.context)
        note_delete = response.context['note']
        self.assertEqual(note_delete.text, self.NOTE_TEXT)
        self.assertEqual(note_delete.title, self.NOTE_TITLE)

    def test_authoraized_client_has_form_for_add_note(self):
        self.add_url = reverse('notes:add')
        response = self.author_client.get(self.add_url)
        self.assertIn('form', response.context)

    def test_authoraized_client_has_form_for_edit_note(self):
        self.edit_url = reverse('notes:edit', args=(self.note.slug,))
        response = self.author_client.get(self.edit_url)
        self.assertIn('form', response.context)
