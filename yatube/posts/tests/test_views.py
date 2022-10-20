import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, Follow


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
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
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author_post = PostViewTests.user
        self.author.force_login(self.author_post)
        cache.clear()

    def test_view_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        pages_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=[PostViewTests.group.slug]):
                'posts/group_list.html',
            reverse('posts:profile',
                    args=[PostViewTests.post.author.username]):
                'posts/profile.html',
            reverse('posts:post_detail', args=[PostViewTests.post.id]):
                'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit', args=[PostViewTests.post.id]):
                'posts/create_post.html',
        }
        for reverse_name, template in pages_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_view_index_uses_correct_context(self):
        """Проверка контекста на главной странице."""
        post = Post.objects.all()
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['page_obj'][-1].text,
                         post.get(
                             id=response.context['page_obj'][-1].id).text)
        self.assertEqual(response.context['page_obj'][-1].image,
                         post.get(
                             id=response.context['page_obj'][-1].id).image)

    def test_view_group_list_correct_context(self):
        """Проверка контекста на странице группы."""
        post = Post.objects.all()
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[PostViewTests.group.slug]))
        self.assertIn('page_obj' and 'group', response.context)
        self.assertEqual(response.context.get('group', 'page_obj').slug,
                         PostViewTests.group.slug)
        self.assertEqual(response.context['page_obj'][-1].image,
                         post.get(
                             id=response.context['page_obj'][-1].id).image)

    def test_view_profile_correct_context(self):
        """Проверка контекста на странице профайла пользователя."""
        post = Post.objects.all()
        response = self.authorized_client.get(
            reverse('posts:profile',
                    args=[PostViewTests.post.author.username]))
        self.assertIn('page_obj' and 'author', response.context)
        self.assertEqual(response.context.get('author', 'page_obj').username,
                         PostViewTests.post.author.username)
        self.assertEqual(response.context['page_obj'][-1].image,
                         post.get(
                             id=response.context['page_obj'][-1].id).image)

    def test_view_post_detail_uses_correct_context(self):
        """Проверка контекста на странице об информации о посте."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[PostViewTests.post.id]))
        self.assertIn('post' and 'form' and 'comments', response.context)
        self.assertEqual(
            response.context.get('post', 'form' and 'comments').id,
            PostViewTests.post.id)
        self.assertEqual(
            response.context.get('post', 'form' and 'comments').image,
            PostViewTests.post.image)

    def test_view_post_create_uses_correct_context(self):
        """Проверка контекста на странице создания поста."""
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertIn('form', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_view_post_edit_uses_correct_context(self):
        """Проверка контекста на странице редактирования поста."""
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        response = self.author.get(reverse('posts:post_edit',
                                           args=[PostViewTests.post.id]))
        self.assertIn('form', response.context)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_in_pages(self):
        """Проверка создания поста."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', args=[PostViewTests.group.slug]),
            reverse('posts:profile', args=[PostViewTests.post.author.username])
        ]

        for page in pages:
            response = self.author.get(page)
            post = response.context['page_obj'][0]
            self.assertEqual(post.text, 'Тестовый пост')
            self.assertEqual(post.author.username,
                             PostViewTests.post.author.username)
            self.assertEqual(post.group.slug,
                             PostViewTests.group.slug)

    def test_cache_index(self):
        """Проверка работы кэша на главной странице."""
        post_0 = Post.objects.create(
            text='Тестовый пост',
            author=self.user)
        response_0 = self.authorized_client.get(
            reverse('posts:index')).content
        post_0.delete()
        response_1 = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(response_0, response_1)
        cache.clear()
        response_2 = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(response_1, response_2)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Тестовое описание',
            slug='test-slug'
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
        cls.post = [
            Post(
                text=f'Тестовый пост {i}',
                author=cls.user,
                group=cls.group,
                image=cls.uploaded,
            )
            for i in range(1, 14)
        ]
        Post.objects.bulk_create(cls.post)

        cls.response_pages = [
            reverse('posts:index'),
            reverse('posts:group_list',
                    args=[PaginatorViewsTests.group.slug]),
            reverse('posts:profile', args=['auth'])
        ]

    def setUp(self):
        self.author = Client()
        self.author_post = PaginatorViewsTests.user
        self.author.force_login(self.author_post)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Проверка количества переданных записей на первой странице."""
        for page in self.response_pages:
            with self.subTest(reverse_name=page):
                response = self.author.get(page)
                self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_second_page_contains_three_records(self):
        """Проверка количества переданных записей на второй странице."""
        for page in self.response_pages:
            with self.subTest(reverse_name=page):
                response = self.author.get(page + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')), 3)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(
            username='author',
        )
        cls.follower = User.objects.create(
            username='follower',
        )
        cls.post = Post.objects.create(
            text='Подписывайтесь',
            author=cls.author,
        )

    def setUp(self):
        self.author_client = Client()
        self.author_client.force_login(self.follower)
        self.follower_client = Client()
        self.follower_client.force_login(self.author)

    def test_subscribe_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        self.follower_client.post(reverse('posts:profile_follow',
                                          kwargs={'username': self.follower}))
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.follower.id)
        self.assertEqual(follow.user_id, self.author.id)

    def test_unsubscribe_from_user(self):
        """Проверка отписки от пользователя."""
        Follow.objects.create(
            user=self.author,
            author=self.follower)
        count_follow = Follow.objects.count()
        self.follower_client.post(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.follower}))
        self.assertEqual(Follow.objects.count(), count_follow - 1)

    def test_follow_on_authors(self):
        """Проверка наличия постов у подписчиков."""
        post = Post.objects.create(
            text='Подписывайтесь',
            author=self.author,
        )
        Follow.objects.create(
            user=self.follower,
            author=self.author,
        )
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_notfollow_on_authors(self):
        """Проверка наличия постов у неподписчиков."""
        post = Post.objects.create(
            text='Подписывайтесь',
            author=self.author,
        )
        response = self.author_client.get(reverse('posts:follow_index'))
        self.assertNotIn(post, response.context['page_obj'].object_list)
