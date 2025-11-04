from datetime import timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils.timezone import now

from exhibition.models import Exhibitions, Portfolio, Exhibitors, Jury
from .models import JuryRating, Rating


class JuryRatingTestCase(TestCase):
	"""Тесты для функционала оценок жюри"""

	def setUp(self):
		"""Подготовка тестовых данных"""
		self.client = Client()
		
		# Создаем пользователей
		self.jury_user = User.objects.create_user(
			username='jury1',
			email='jury@test.com',
			password='testpass123',
			first_name='Test',
			last_name='Jury'
		)
		
		self.regular_user = User.objects.create_user(
			username='user1',
			email='user@test.com',
			password='testpass123'
		)
		
		self.exhibitor_user = User.objects.create_user(
			username='exhibitor1',
			email='exhibitor@test.com',
			password='testpass123'
		)
		
		# Создаем жюри (используем прямое создание в БД для тестов)
		from django.test import RequestFactory
		factory = RequestFactory()
		request = factory.get('/')
		
		self.jury = Jury(
			user=self.jury_user,
			name='Test Jury Member',
			slug='test-jury'
		)
		self.jury.save(request)
		
		# Создаем участника
		self.exhibitor = Exhibitors(
			user=self.exhibitor_user,
			name='Test Exhibitor',
			slug='test-exhibitor'
		)
		self.exhibitor.save(request)
		
		# Создаем активную выставку (не завершена)
		self.active_exhibition = Exhibitions.objects.create(
			title='Active Exhibition 2024',
			slug='2024',
			date_start=now().date() - timedelta(days=10),
			date_end=now().date() + timedelta(days=10)
		)
		
		# Создаем завершенную выставку
		self.past_exhibition = Exhibitions.objects.create(
			title='Past Exhibition 2023',
			slug='2023',
			date_start=now().date() - timedelta(days=365),
			date_end=now().date() - timedelta(days=300)
		)
		
		# Создаем портфолио для активной выставки
		self.portfolio_active = Portfolio.objects.create(
			owner=self.exhibitor,
			exhibition=self.active_exhibition,
			title='Test Project Active',
			project_id=1
		)
		
		# Создаем портфолио для завершенной выставки
		self.portfolio_past = Portfolio.objects.create(
			owner=self.exhibitor,
			exhibition=self.past_exhibition,
			title='Test Project Past',
			project_id=2
		)

	def test_jury_member_identification(self):
		"""Тест: проверка идентификации члена жюри"""
		from .views import is_jury_member
		
		self.assertTrue(is_jury_member(self.jury_user))
		self.assertFalse(is_jury_member(self.regular_user))
		self.assertFalse(is_jury_member(self.exhibitor_user))

	def test_jury_can_rate_active_exhibition(self):
		"""Тест: член жюри может оценить проект активной выставки"""
		self.client.login(username='jury1', password='testpass123')
		
		response = self.client.post(
			reverse('rating:add-jury-rating'),
			{
				'star': 5,
				'portfolio': self.portfolio_active.id,
				'exhibition': self.active_exhibition.id
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest'
		)
		
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data['status'], 'success')
		self.assertEqual(data['score'], 5)
		
		# Проверяем, что оценка сохранена
		self.assertTrue(
			JuryRating.objects.filter(
				jury=self.jury_user,
				portfolio=self.portfolio_active,
				exhibition=self.active_exhibition
			).exists()
		)

	def test_jury_cannot_rate_past_exhibition(self):
		"""Тест: член жюри не может оценить проект завершенной выставки"""
		self.client.login(username='jury1', password='testpass123')
		
		response = self.client.post(
			reverse('rating:add-jury-rating'),
			{
				'star': 5,
				'portfolio': self.portfolio_past.id,
				'exhibition': self.past_exhibition.id
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest'
		)
		
		self.assertEqual(response.status_code, 400)
		data = response.json()
		self.assertEqual(data['status'], 'error')
		self.assertIn('завершена', data['message'])

	def test_regular_user_cannot_rate_as_jury(self):
		"""Тест: обычный пользователь не может выставлять оценки жюри"""
		self.client.login(username='user1', password='testpass123')
		
		response = self.client.post(
			reverse('rating:add-jury-rating'),
			{
				'star': 5,
				'portfolio': self.portfolio_active.id,
				'exhibition': self.active_exhibition.id
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest'
		)
		
		self.assertEqual(response.status_code, 403)
		data = response.json()
		self.assertEqual(data['status'], 'error')

	def test_jury_rating_update(self):
		"""Тест: член жюри может обновить свою оценку"""
		# Создаем первую оценку
		JuryRating.objects.create(
			jury=self.jury_user,
			portfolio=self.portfolio_active,
			exhibition=self.active_exhibition,
			star=3,
			ip='127.0.0.1'
		)
		
		self.client.login(username='jury1', password='testpass123')
		
		# Обновляем оценку
		response = self.client.post(
			reverse('rating:add-jury-rating'),
			{
				'star': 5,
				'portfolio': self.portfolio_active.id,
				'exhibition': self.active_exhibition.id
			},
			HTTP_X_REQUESTED_WITH='XMLHttpRequest'
		)
		
		self.assertEqual(response.status_code, 200)
		data = response.json()
		self.assertEqual(data['message'], 'Оценка обновлена')
		
		# Проверяем, что оценка обновлена
		rating = JuryRating.objects.get(
			jury=self.jury_user,
			portfolio=self.portfolio_active
		)
		self.assertEqual(rating.star, 5)

	def test_jury_rating_separate_from_regular_rating(self):
		"""Тест: оценки жюри не смешиваются с обычными оценками"""
		# Создаем оценку жюри
		JuryRating.objects.create(
			jury=self.jury_user,
			portfolio=self.portfolio_active,
			exhibition=self.active_exhibition,
			star=5,
			ip='127.0.0.1'
		)
		
		# Создаем обычную оценку
		Rating.objects.create(
			user=self.regular_user,
			portfolio=self.portfolio_active,
			star=3,
			ip='127.0.0.1'
		)
		
		# Проверяем, что средний балл обычных оценок не включает оценки жюри
		regular_stats = Rating.calculate(self.portfolio_active)
		self.assertEqual(regular_stats.average, 3.0)
		
		# Проверяем среднюю оценку жюри отдельно
		jury_stats = JuryRating.calculate_jury_average(
			self.portfolio_active.id,
			self.active_exhibition.id
		)
		self.assertEqual(jury_stats['average'], 5.0)
		self.assertEqual(jury_stats['count'], 1)

	def test_jury_rating_unique_constraint(self):
		"""Тест: уникальность оценки жюри (один член жюри - одна оценка на выставку)"""
		# Создаем первую оценку
		JuryRating.objects.create(
			jury=self.jury_user,
			portfolio=self.portfolio_active,
			exhibition=self.active_exhibition,
			star=4,
			ip='127.0.0.1'
		)
		
		# Проверяем, что нельзя создать дубликат через Django ORM
		from django.db import IntegrityError
		with self.assertRaises(IntegrityError):
			JuryRating.objects.create(
				jury=self.jury_user,
				portfolio=self.portfolio_active,
				exhibition=self.active_exhibition,
				star=5,
				ip='127.0.0.1'
			)

	def test_calculate_jury_average_multiple_ratings(self):
		"""Тест: расчет средней оценки жюри с несколькими оценками"""
		# Создаем второго члена жюри
		jury_user2 = User.objects.create_user(
			username='jury2',
			password='testpass123'
		)
		
		from django.test import RequestFactory
		factory = RequestFactory()
		request = factory.get('/')
		
		jury2 = Jury(
			user=jury_user2,
			name='Second Jury',
			slug='jury2'
		)
		jury2.save(request)
		
		# Создаем оценки от разных членов жюри
		JuryRating.objects.create(
			jury=self.jury_user,
			portfolio=self.portfolio_active,
			exhibition=self.active_exhibition,
			star=5,
			ip='127.0.0.1'
		)
		
		JuryRating.objects.create(
			jury=jury_user2,
			portfolio=self.portfolio_active,
			exhibition=self.active_exhibition,
			star=3,
			ip='127.0.0.1'
		)
		
		# Проверяем средний балл
		jury_stats = JuryRating.calculate_jury_average(
			self.portfolio_active.id,
			self.active_exhibition.id
		)
		self.assertEqual(jury_stats['average'], 4.0)
		self.assertEqual(jury_stats['count'], 2)

	def test_project_detail_view_jury_context(self):
		"""Тест: контекст страницы проекта содержит информацию о возможности оценки жюри"""
		self.client.login(username='jury1', password='testpass123')
		
		url = reverse('exhibition:project-detail-url', kwargs={
			'owner': self.exhibitor.slug,
			'project_id': self.portfolio_active.project_id
		})
		
		response = self.client.get(url, HTTP_HOST='testserver', HTTP_USER_AGENT='Mozilla/5.0')
		
		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['is_jury'])
		self.assertTrue(response.context['jury_can_rate'])
		self.assertTrue(response.context['exhibition_active'])
		self.assertEqual(response.context['jury_average'], 0)
		self.assertEqual(response.context['jury_count'], 0)
