from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from posts.models import Group, Post, User


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.group = Group.objects.create(
            title='No',
            slug='No',
            description='No'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.anon = Client()
        self.user = User.objects.create_user(username='NoName')
        self.auth = Client()
        self.auth.force_login(self.user)
        cache.clear()

    def test_homepage(self):
        response = self.anon.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_template(self):
        template_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.post.group}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html'
        }

        if self.anon:
            for address, template in template_url_names.items():
                with self.subTest(address=address):
                    if self.anon:
                        response = self.anon.get(address)
                        self.assertTemplateUsed(response, template)

        elif self.auth:
            address = '/create/'
            with self.subTest(address=address):
                response = self.auth.get(address)
                self.assertTemplateUsed(response, 'posts/create_post.html')

        elif response.user == self.post.author:
            address = '/posts/<post_id>/edit/'
            with self.subTest(address=address):
                response = self.user.get(address)
                self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_404_custom(self):
        address = '/posts/wwwwwoworoworwo'
        response = self.anon.get(address)
        self.assertTemplateUsed(response, 'core/404.html')
