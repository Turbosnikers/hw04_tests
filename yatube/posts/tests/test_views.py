from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from posts.views import POSTS_COUNT


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Текст поста',
            slug='test_slug',
            description='Описание поста'
        )
        cls.group2 = Group.objects.create(
            title='Текст поста',
            slug='test_slug2',
            description='Описание поста'
        )
        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый текст {num}',
                group=cls.group
            )
            for num in range(1, 21)]
        )
        cls.post = Post.objects.all()[0]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_uses_correct_template(self):
        response = self.client.get(reverse('posts:index'))
        self.assertTemplateUsed(response, 'posts/index.html')

    def test_pages_uses_correct_template(self):
        post_id = PostPagesTests.post.id
        group_slug = PostPagesTests.group.slug
        user_test = PostPagesTests.user
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'slug': group_slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': user_test})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post_id})
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_edit_page(self):
        post_id = PostPagesTests.post.id
        templates_pages_names = {
            'posts/create_post.html': (
                reverse('posts:post_edit', kwargs={'post_id': post_id}))
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_context_paginator(self):
        response = self.authorized_client.get(reverse('posts:index'))
        page_obj = response.context.get('page_obj')
        self.assertEqual(len(page_obj), POSTS_COUNT)

    def test_group_posts_context_paginator(self):
        group_slug = PostPagesTests.group.slug
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_slug}))
        self.assertEqual(len(response.context['page_obj']), POSTS_COUNT)

    def test_post_not_in_wrong_group(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', args=[PostPagesTests.group2.slug])
        )
        self.assertNotIn(self.post, response.context.get('page_obj'))

    def test_post_detail_pages_show_correct_context(self):
        post_id = PostPagesTests.post.id
        user_test = PostPagesTests.user
        post_text = PostPagesTests.post.text
        group_slug = PostPagesTests.group.slug
        response = (self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})))
        self.assertEqual(response.context.get('post').author, user_test)
        self.assertEqual(response.context.get(
            'post').text, post_text)
        self.assertEqual(response.context.get('post').group.slug, group_slug)

    def test_post_create_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        post_id = PostPagesTests.post.id
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': post_id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_list_context(self):
        group_slug = PostPagesTests.group.slug
        group_title = PostPagesTests.group.title
        group_description = PostPagesTests.group.description
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': group_slug}))
        obj_1 = response.context['group']
        group_title_test = obj_1.title
        group_slug_test = obj_1.slug
        group_description_test = obj_1.description
        self.assertEqual(group_title_test, group_title)
        self.assertEqual(group_description_test, group_description)
        self.assertEqual(group_slug_test, group_slug)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user_2')
        cls.group = Group.objects.create(
            title='Текст поста',
            slug='test_slug_2',
            description='Описание поста'
        )
        Post.objects.bulk_create([
            Post(
                author=cls.user,
                text=f'Тестовый текст {num}',
                group=cls.group
            )
            for num in range(1, 25)]
        )

    def test_first_page_contains_ten_records(self):
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_COUNT)

    def test_second_page_contains_three_records(self):
        posts = Post.objects.all()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']), POSTS_COUNT % len(posts))
