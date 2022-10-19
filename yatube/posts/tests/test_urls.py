from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from posts.models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):
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
            author=cls.user,
            text='Тестовый пост',
        )

        cls.http_url_names_for_guest = {
            HTTPStatus.OK: '/',
            HTTPStatus.OK: f'/group/{PostURLTests.group.slug}/',
            HTTPStatus.OK: f'/profile/{PostURLTests.post.author.username}/',
            HTTPStatus.OK: f'/posts/{PostURLTests.post.id}/',
            HTTPStatus.NOT_FOUND: '/unexisting_page/',
        }
        cls.http_url_names_for_authorized_client = {
            HTTPStatus.OK: '/create/',
        }
        cls.http_url_names_for_authorized_client.update(
            cls.http_url_names_for_guest)
        cls.http_url_names_for_author = {
            HTTPStatus.OK: f'/posts/{PostURLTests.post.id}/edit/',
        }
        cls.http_url_names_for_author.update(
            cls.http_url_names_for_authorized_client)

        cls.url_templates_names_for_guest = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.post.author.username}/':
                'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
        }
        cls.url_templates_names_for_authorized_client = {
            '/create/': 'posts/create_post.html',
        }
        cls.url_templates_names_for_authorized_client.update(
            cls.url_templates_names_for_guest)
        cls.url_templates_names_for_author = {
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
        }
        cls.url_templates_names_for_author.update(
            cls.url_templates_names_for_authorized_client)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author = Client()
        self.author_post = PostURLTests.user
        self.author.force_login(self.author_post)

    def test_post_for_guest_url_exists_at_desired_location(self):
        """Проверка доступности страниц в приложении posts для гостя."""
        for http, address in self.http_url_names_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, http)

    def test_post_for_authorized_client_url_exists_at_desired_location(self):
        """Проверка доступности страниц в приложении posts для
        авторизованного пользователя.
        """
        for http, address in self.http_url_names_for_authorized_client.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, http)

    def test_post_for_author_url_exists_at_desired_location(self):
        """Проверка доступности страниц в приложении posts для автора поста."""
        for http, address in self.http_url_names_for_author.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertEqual(response.status_code, http)

    def test_post_for_guest_urls_uses_correct_template(self):
        """URL-адрес в приложении posts для гостя использует
        соответствующий шаблон.
        """
        for address, template in self.url_templates_names_for_guest.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_for_authorized_client_urls_uses_correct_template(self):
        """URL-адрес в приложении posts авторизованного пользователя
        использует соответствующий шаблон.
        """
        for address, template in (
                self.url_templates_names_for_authorized_client.items()):
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_for_author_urls_uses_correct_template(self):
        """URL-адрес в приложении posts для автора поста использует
        соответствующий шаблон.
        """
        for address, template in self.url_templates_names_for_author.items():
            with self.subTest(address=address):
                response = self.author.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_create_for_guest(self):
        """Страница по адресу /create/ перенаправит гостя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_core_for_guest_404(self):
        """Проверка использования кастомного шаблона при вызове
        несуществующей страницы (ошибка 404).
        """
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
