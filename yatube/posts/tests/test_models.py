from django.test import TestCase
from mixer.backend.django import mixer

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = mixer.blend(Group)
        cls.post = Post.objects.create(
            text='Hello, subsribers',
            author=cls.user,
        )

    def test_object_name_post_is_correct(self):
        post = self.post
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_post, str(post))

    def test_object_name_group_is_correct(self):
        group = self.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))

    def test_verbose_name_is_correct(self):
        post = self.post
        verbose_names = {
            'text': 'Tекст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, expected_value in verbose_names.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name,
                    expected_value
                )

    def test_help_text_is_correct(self):
        post = self.post
        fields_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, expected_value in fields_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text,
                    expected_value
                )
