from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse
from posts.constants import FIRST_TEN
from posts.models import Comment, Follow, Group, Post, User


class PostViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(title='Test',
                                         slug='test',
                                         description='test',)
        cls.group2 = Group.objects.create(title='Test2',
                                          slug='test2',
                                          description='test2',)
        cls.author = User.objects.create(username='Author')

        cls.small_gif = (            
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

        bulk_list = []
        for i in range(1, FIRST_TEN + 2):
            bulk_list.append(Post(
                text='Тест' + str(i),
                author=cls.author,
                group=cls.group,
                image=uploaded,
            ))
        cls.posts = Post.objects.bulk_create(bulk_list)
        cache.clear()


    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Test')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        template_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': 'test'}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': 'Author'}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={'post_id': '1'}),
            'posts/create_post.html': reverse('posts:post_create'),
        }

        for template, reverse_name in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_redirect(self):
        template_pages_names = {
            reverse('posts:post_edit', kwargs={'post_id': '1'}):
            'posts/create_post.html'}

        for reverse_name, template in template_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if not self.assertRedirects:
                    post = response.context['post']
                    if response.user == post.author:
                        self.assertTemplateUsed(response, template)
                    else:
                        self.assertRedirects(response,
                                             reverse
                                             ('posts:post_detail',
                                              kwargs={'post_id': '1'}))

    def test_index_page_shows_correct_context(self):
        test_list = Post.objects.select_related('author', 'group')
        response = self.authorized_client.get(reverse('posts:index'))
        post_list = response.context['post_list']
        self.assertQuerysetEqual(post_list, test_list, lambda x: x)

    def test_group_posts_page_shows_correct_context(self):
        group = get_object_or_404(Group, slug='test')
        test_post = group.posts.select_related('author')
        response = self.authorized_client.get(reverse('posts:group_list',
                                                      kwargs={'slug': 'test'}))
        posts = response.context['posts']
        self.assertQuerysetEqual(test_post, posts, transform=lambda x: x)

    def test_profile_page_shows_correct_context(self):
        author = get_object_or_404(User, username='Author')
        test_post = Post.objects.filter(author=author)
        response = self.authorized_client.get(reverse('posts:profile',
                                              kwargs={'username': 'Author'}))
        posts = response.context['post_list']
        self.assertQuerysetEqual(test_post, posts, transform=lambda x: x)

    def test_post_detail_page_shows_correct_context(self):
        one_post = get_object_or_404(Post, id='1')
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': 1}))
        test_post = response.context['one_post']
        self.assertEqual(one_post, test_post)

    def test_post_create_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_one_record(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test2_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test2_second_page_contains_one_record(self):
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test3_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'Author'}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test3_second_page_contains_one_record(self):
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username':
                                                   'Author'})
                                   + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_group_added(self):
        one_post = get_object_or_404(Post, id='1')
        response_dict = {reverse('posts:index'): 'post_list',
                         reverse('posts:group_list',
                         kwargs={'slug': 'test'}): 'posts',
                         reverse('posts:profile',
                         kwargs={'username': 'Author'}): 'post_list', }
        for page, context_variable in response_dict.items():
            with self.subTest(page=page):
                response = self.client.get(page)
                if one_post.group:
                    self.assertIn(one_post, response.context[context_variable])

    def test_group_not_added(self):
        one_post = get_object_or_404(Post, id='1')
        response = self.client.get(reverse('posts:group_list',
                                           kwargs={'slug': 'test2'}))
        self.assertNotIn(one_post, response.context['posts'])

    def test_image_shown_index(self):  
        one_post = get_object_or_404(Post, id='1')
        response = self.authorized_client.get(reverse('posts:index'))
        test_post = response.context['post_list'][10]
        self.assertEqual(one_post.image, test_post.image)

    def test_image_shown_profile(self):
        one_post = get_object_or_404(Post, id='1')
        response = self.authorized_client.get(reverse('posts:profile',
                                                      kwargs={'username': 'Author'}))
        test_post = response.context['post_list'][10]
        self.assertEqual(one_post.image, test_post.image)

    def test_image_shown_group_list(self):
       one_post = get_object_or_404(Post, id='1')
       response = self.authorized_client.get(reverse('posts:index'))
       test_post = response.context['post_list'][10]
       self.assertEqual(one_post.image, test_post.image)

    def test_image_shown_post_detail(self):
        one_post = get_object_or_404(Post, id='1')
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': 1}))
        test_post = response.context['one_post']
        self.assertEqual(one_post.image, test_post.image)
    
    def test_comments_shown_post_detail(self):
        one_post = get_object_or_404(Post, id='1')
        response = self.authorized_client.get(reverse('posts:post_detail',
                                                      kwargs={'post_id': 1}))
        test_post = response.context['one_post']
        self.assertEqual(one_post.comments, test_post.comments)

    def test_cache_works(self):
        response = self.authorized_client.get(reverse('posts:index'))
        with self.assertNumQueries(0):
            Post.objects.select_related('author', 'group')
    
    def test_cache_after_delete(self):
        page_first = self.authorized_client.get(reverse('posts:index'))
        Post.objects.create(text='SSS', author=self.user, group=self.group)
        page_second = self.authorized_client.get(reverse('posts:index'))
        cache.clear()
        page_clear = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(page_first.content, page_second.content)
        self.assertNotEqual(page_first.content, page_clear.content)

    def test_auth_follow_unfollow(self):
        author = get_object_or_404(User, username=self.author.username)
        Follow.objects.create(author=author, user=self.user)
        post_list = Post.objects.filter(author__following__user=self.user)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertListEqual(list(post_list), list(response.context['post_list']))
        unfollow = Follow.objects.filter(author=author, user=self.user)
        unfollow.delete()
        self.assertNotIn(unfollow, list(response.context['post_list']))

