from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.db import models
from .models import Task
from .views import (
    TaskListView,
    TaskDetailView,
    TaskCreateView,
    TaskUpdateView,
    TaskDeleteView,
)


class TaskModelTest(TestCase):  # 10점
    def setUp(self):
        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            due_date=timezone.now().date() + timedelta(days=1),
        )

    def test_task_creation(self):
        # Task 객체가 올바르게 생성되었는지 확인 (1점)
        self.assertTrue(isinstance(self.task, Task))
        self.assertEqual(str(self.task), "Test Task")

    def test_task_ordering(self):
        # Task 객체들이 생성 시간의 역순으로 정렬되는지 확인 (3점)
        Task.objects.create(
            title="Another Task",
            description="This is another test task",
            due_date=timezone.now().date() + timedelta(days=2),
        )
        tasks = Task.objects.all()
        self.assertEqual(tasks.first().title, "Another Task")
        self.assertEqual(tasks.last().title, "Test Task")

    def test_is_overdue(self):
        # is_overdue 메서드가 올바르게 작동하는지 확인 (3점)
        self.assertFalse(self.task.is_overdue())
        self.task.due_date = timezone.now().date() - timedelta(days=1)
        self.task.save()
        self.assertTrue(self.task.is_overdue())

    def test_field_constraints(self):
        # Task 모델의 필드 제약 조건을 확인 (3점)
        task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            due_date=timezone.now().date(),
        )

        self.assertEqual(task._meta.get_field("title").max_length, 200)
        self.assertFalse(task.completed)
        self.assertIsNotNone(task.created_at)
        self.assertIsInstance(task._meta.get_field("due_date"), models.DateField)


class TaskViewsTest(TestCase):  # 25점
    def setUp(self):
        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            due_date=timezone.now().date() + timedelta(days=1),
        )

    def test_task_list_view(self):
        # TaskListView가 올바르게 렌더링되는지 확인 (1점)
        response = self.client.get(reverse("tasks:task-list"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["view"], TaskListView)

    def test_task_list_view_queryset(self):
        # TaskListView의 쿼리셋이 완료되지 않은 최신 작업을 먼저 반환하는지 확인 (5점)
        Task.objects.create(
            title="Completed Task",
            description="This is a completed task",
            due_date=timezone.now().date() + timedelta(days=1),
            completed=True,
        )
        new_task = Task.objects.create(
            title="New Incomplete Task",
            description="This is a new incomplete task",
            due_date=timezone.now().date() + timedelta(days=2),
        )

        response = self.client.get(reverse("tasks:task-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["object_list"].first(), new_task)
        self.assertNotIn(
            "Completed Task", [task.title for task in response.context["object_list"]]
        )

    def test_task_detail_view(self):
        # TaskDetailView가 올바르게 렌더링되는지 확인 (1점)
        response = self.client.get(reverse("tasks:task-detail", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["view"], TaskDetailView)
        self.assertEqual(response.context["object"], self.task)

    def test_task_create_view(self):
        # TaskCreateView가 올바르게 렌더링되는지 확인 (1점)
        response = self.client.get(reverse("tasks:task-create"))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["view"], TaskCreateView)

    def test_task_create_view_fields(self):
        # TaskCreateView가 필요한 필드를 모두 포함하고 있는지 확인 (3점)
        response = self.client.get(reverse("tasks:task-create"))
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("title", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("completed", form.fields)
        self.assertIn("due_date", form.fields)

    def test_task_update_view_rendering(self):
        # TaskUpdateView가 올바르게 렌더링되는지 확인 (1점)
        response = self.client.get(reverse("tasks:task-update", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["view"], TaskUpdateView)

    def test_task_update_view_form_fields(self):
        # TaskUpdateView가 필요한 필드를 모두 포함하고 있는지 확인 (3점)
        response = self.client.get(reverse("tasks:task-update", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)

        form = response.context["form"]
        self.assertIn("title", form.fields)
        self.assertIn("description", form.fields)
        self.assertIn("completed", form.fields)
        self.assertIn("due_date", form.fields)

    def test_task_update_view_updates_task(self):
        # TaskUpdateView가 실제로 Task를 수정하는지 확인(3점)
        updated_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "due_date": timezone.now().date(),
            "completed": True,
        }
        self.client.post(
            reverse("tasks:task-update", args=[self.task.id]), data=updated_data
        )

        self.task.refresh_from_db()

        self.assertEqual(self.task.title, updated_data["title"])
        self.assertEqual(self.task.description, updated_data["description"])
        self.assertEqual(self.task.completed, updated_data["completed"])
        self.assertEqual(self.task.due_date, updated_data["due_date"])

    def test_task_update_view_redirects_after_update(self):
        # TaskUpdateView가 수정 후 개별 조회하는 페이지로 리다이렉트하는지 확인 (1점)
        updated_data = {
            "title": "Updated Task",
            "description": "Updated description",
            "due_date": timezone.now().date(),
            "completed": True,
        }
        response = self.client.post(
            reverse("tasks:task-update", args=[self.task.id]), data=updated_data
        )

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response, reverse("tasks:task-detail", args=[self.task.id])
        )

    def test_task_delete_view(self):
        # TaskDeleteView가 올바르게 렌더링되는지 확인 (2점)
        response = self.client.get(reverse("tasks:task-delete", args=[self.task.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["view"], TaskDeleteView)

    def test_task_delete_view_deletes_task(self):
        # TaskDeleteView가 실제로 Task를 삭제하는지 확인 (2점)
        task_id = self.task.id
        self.client.post(reverse("tasks:task-delete", args=[task_id]))

        with self.assertRaises(Task.DoesNotExist):
            Task.objects.get(id=task_id)

    def test_task_delete_view_redirects_after_delete(self):
        # TaskDeleteView가 삭제 후 목록으로 리다이렉트하는지 확인 (1점)
        response = self.client.post(reverse("tasks:task-delete", args=[self.task.id]))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tasks:task-list"))


class TaskURLsTest(TestCase):  # 5점
    def setUp(self):
        self.task = Task.objects.create(
            title="Test Task",
            description="This is a test task",
            due_date=timezone.now().date() + timedelta(days=1),
        )

    def test_task_list_url(self):
        # Task 목록 URL이 올바른지 확인 (1점)
        url = reverse("tasks:task-list")
        self.assertEqual(url, "/")

    def test_task_detail_url(self):
        # Task 상세 조회 URL이 올바른지 확인 (1점)
        url = reverse("tasks:task-detail", args=[self.task.id])
        self.assertEqual(url, f"/{self.task.id}/")

    def test_task_create_url(self):
        # Task 생성 URL이 올바른지 확인 (1점)
        url = reverse("tasks:task-create")
        self.assertEqual(url, "/create/")

    def test_task_update_url(self):
        # Task 수정 URL이 올바른지 확인 (1점)
        url = reverse("tasks:task-update", args=[self.task.id])
        self.assertEqual(url, f"/{self.task.id}/update/")

    def test_task_delete_url(self):
        # Task 삭제 URL이 올바른지 확인 (1점)
        url = reverse("tasks:task-delete", args=[self.task.id])
        self.assertEqual(url, f"/{self.task.id}/delete/")
