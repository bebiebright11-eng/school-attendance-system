from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

User = get_user_model()


class UserModelTest(TestCase):
    """Tests for the custom User model in the accounts app."""

    def _make_user(self, username='testuser', email='test@example.com', role=''):
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            role=role,
        )

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_create_user_basic(self):
        user = self._make_user()
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('testpass123'))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)

    def test_create_user_with_role(self):
        user = self._make_user(role=User.Role.TEACHER)
        self.assertEqual(user.role, User.Role.TEACHER)

    # ------------------------------------------------------------------
    # Role choices
    # ------------------------------------------------------------------

    def test_all_role_choices_are_valid(self):
        roles = [User.Role.ADMINISTRATOR, User.Role.TEACHER]
        for i, role in enumerate(roles):
            user = self._make_user(
                username=f'user_{i}',
                email=f'user{i}@example.com',
                role=role,
            )
            self.assertEqual(user.role, role)

    def test_role_convenience_properties(self):
        admin = self._make_user(username='admin', email='admin@e.com', role=User.Role.ADMINISTRATOR)
        teacher = self._make_user(username='teacher', email='teacher@e.com', role=User.Role.TEACHER)

        self.assertTrue(admin.is_administrator)
        self.assertFalse(admin.is_teacher)

        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_administrator)

    def test_parent_role_does_not_exist(self):
        """Guardian is a domain entity, not a User role. PARENT must not be in Role choices."""
        role_values = [r.value for r in User.Role]
        self.assertNotIn('parent', role_values)

    def test_class_parent_role_does_not_exist(self):
        """Class Parent is a Teacher responsibility, not a User role."""
        role_values = [r.value for r in User.Role]
        self.assertNotIn('class_parent', role_values)

    # ------------------------------------------------------------------
    # Uniqueness
    # ------------------------------------------------------------------

    def test_email_must_be_unique(self):
        self._make_user()
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='other',
                email='test@example.com',  # duplicate
                password='pass',
            )

    def test_username_must_be_unique(self):
        self._make_user()
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='testuser',  # duplicate
                email='other@example.com',
                password='pass',
            )

    # ------------------------------------------------------------------
    # __str__
    # ------------------------------------------------------------------

    def test_str_with_full_name_and_role(self):
        user = self._make_user(role=User.Role.TEACHER)
        user.first_name = 'Jane'
        user.last_name = 'Doe'
        user.save()
        self.assertIn('Jane Doe', str(user))
        self.assertIn('Teacher', str(user))

    def test_str_without_full_name_falls_back_to_username(self):
        user = self._make_user()
        self.assertIn('testuser', str(user))

    def test_str_with_no_role_shows_no_role_label(self):
        user = self._make_user(role='')
        self.assertIn('No role', str(user))
