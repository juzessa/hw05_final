import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.post = Post.objects.create(text='Тест1',
                                       author=cls.author,)
        cls.user = User.objects.create_user(username='Test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cache.clear()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        group = Group.objects.create(title='Test',
                                     slug='test',
                                     description='test',)
        self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Что-то такое',
                  'group': group.id},
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Что-то такое',
                group=group.id).exists())

    def test_edit_post(self):
        post = Post.objects.create(text='Тест1',
                                   author=self.author,)
        group = Group.objects.create(title='Test',
                                     slug='test',
                                     description='test',)
        self.post.text = post.text + 'new'
        form_data = {
            'text': post.text,
            'group': group.id
        }

        self.authorized_client.post(
            reverse('posts:post_edit', args=(10,)),
            data=form_data,)
        self.post.refresh_from_db()
        self.assertNotEqual(self.post.text, 'Тест1new')

    def test_image_saved(self):
        """Запись создается вместе с добавленной картинкой"""
        small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                     b'\x01\x00\x80\x00\x00\x00\x00\x00'
                     b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                     b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                     b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                     b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый',
            'image': uploaded
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый',
                image='posts/small.gif'
            ).exists()
        )


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.author = User.objects.create(username='Author')
        cls.post = Post.objects.create(text='Тест1',
                                       author=cls.author,)
        cls.anon = Client()
        cls.user = User.objects.create_user(username='Test')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cache.clear()

    def test_comments_create_only_auth(self):
        response = self.authorized_client.get(reverse('posts:add_comment',
                                                      kwargs={'post_id':
                                                      f'{self.post.pk}'
                                                                       }))
        self.assertRedirects(response,reverse('posts:post_detail',
                                               kwargs={'post_id':
                                              f'{self.post.pk}'}))

    def test_comments_post_detail_shown(self):
        comment = Comment.objects.create(post=self.post,
                                         author=self.author,
                                         text='Wow',)
        form_data = {
            'text': comment.text
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                                                 'post_id': f'{self.post.pk}'}),
                                                  data=form_data,)
        response = self.authorized_client.get(reverse(
                                                      'posts:post_detail',
                                                      kwargs={
                                                      'post_id': f'{self.post.pk}'}))
        self.assertEqual(comment, response.context['comments'][0])
        self.assertEqual(form_data['text'],
                         response.context['comments'][1].text)
