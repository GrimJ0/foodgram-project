import uuid

from django.test import TestCase, Client
from django.urls import reverse
from app.models import User, Recipe, Favorite, ShopList


class TestAuthorizedUsers(TestCase):
    fixtures = ['db.json', ]

    def setUp(self):
        """создание тестового клиента"""
        self.client = Client()

        self.user = User.objects.create_user(
            username='sarah', email='connor@skynet.com', password='test'
        )

        self.client.login(email='connor@skynet.com', password='test')

    def test_home_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['recipes'].count(), 4)

    def test_favorites(self):
        response = self.client.get(reverse('index'))
        html = '''<button class="button button_style_none"
                name="favorites" data-out>
                <span class="icon-favorite"></span></button>'''
        self.assertContains(response, html, count=4, html=True)

        self.recipe = Recipe.objects.all().first()
        Favorite.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.get(reverse('index'))
        self.assertContains(response, html, count=3, html=True)

    def test_purchases(self):
        response = self.client.get(reverse('index'))
        html = '''<button class="button button_style_light-blue"
                name="purchases" data-out><span class="icon-plus button__icon">
                </span>Добавить в покупки</button>'''
        self.assertContains(response, html, count=4, html=True)

        self.recipe = Recipe.objects.all().first()
        ShopList.objects.create(user=self.user, recipe=self.recipe)
        response = self.client.get(reverse('index'))
        self.assertContains(response, html, count=3, html=True)

    def test_tag_filter(self):
        response = self.client.get(reverse('index'), data={'tag': 'BREAKFAST'})
        self.assertEqual(response.context['recipes'].count(), 2)
        response = self.client.get(reverse('index'), data={'tag': ['BREAKFAST', 'LUNCH']})
        self.assertEqual(response.context['recipes'].count(), 3)


class TestUnauthorizedUsers(TestCase):
    fixtures = ['db.json', ]

    def setUp(self):
        """создание тестового клиента"""
        self.client = Client()

    def test_home_page(self):
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['recipes'].count(), 4)

    def test_subscriptions(self):
        response = self.client.get(reverse('index'))
        html = '''<button class="button button_style_none"
                name="favorites" data-out>
                <span class="icon-favorite"></span></button>'''
        self.assertNotContains(response, html, html=True)

    def test_purchases(self):
        response = self.client.get(reverse('index'))
        html = '''<button class="button button_style_light-blue"
                name="purchases" data-out><span class="icon-plus button__icon">
                </span>Добавить в покупки</button>'''
        self.assertContains(response, html, count=4, html=True)

        self.recipe = Recipe.objects.all().first()
        session = self.client.session
        session.update({
            "purchase_id": str(uuid.uuid4()),
        })
        session.save()
        session_key = self.client.session.get('purchase_id')
        ShopList.objects.create(session_key=session_key, recipe=self.recipe)
        response = self.client.get(reverse('index'))
        self.assertContains(response, html, count=3, html=True)

    def test_tag_filter(self):
        response = self.client.get(reverse('index'), data={'tag': 'BREAKFAST'})
        self.assertEqual(response.context['recipes'].count(), 2)
        response = self.client.get(reverse('index'), data={'tag': ['DINNER', 'LUNCH']})
        self.assertEqual(response.context['recipes'].count(), 3)
