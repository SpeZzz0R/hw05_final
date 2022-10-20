import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug2',
            description='Тестовое описание 2'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.form_fields = {
            'text': 'Тестовый пост',
            'group': cls.group.id,
            'image': cls.uploaded,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author_post = PostFormsTests.user
        self.author.force_login(self.author_post)

    def test_form_post_create(self):
        """Проверка создания новой записи в базе данных."""
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=self.form_fields, follow=True)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=self.form_fields['text'],
                                            group=self.group.id,
                                            image='posts/small.gif').exists()
                        )
        self.assertRedirects(response,
                             reverse(
                                 'posts:profile',
                                 args=[PostFormsTests.post.author.username]))
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group_id, self.form_fields['group'])

    def test_form_post_edit(self):
        """Проверка изменения поста в базе данных."""
        post_0 = post_1 = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group,
        )
        response_0 = self.authorized_client.get(
            reverse('posts:group_list', args=[PostFormsTests.group.slug]))
        post_2 = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
            group=self.group2,
        )
        post_0 = post_2
        response_2 = self.authorized_client.get(
            reverse('posts:group_list', args=[PostFormsTests.group.slug]))

        self.author.post(
            reverse('posts:post_edit', args=[PostFormsTests.post.id]),
            data=self.form_fields, follow=True)
        self.assertTrue(Post.objects.filter(text=self.form_fields['text'],
                                            group=self.group.id).exists()
                        )
        self.assertIn(post_1, response_0.context['page_obj'].object_list)
        self.assertNotIn(post_0, response_2.context['page_obj'].object_list)
