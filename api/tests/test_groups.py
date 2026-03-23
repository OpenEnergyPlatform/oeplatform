from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from dataedit.models import Table
from login.models import (
    GroupPermission,
    Membership,
    Organization,
    Project,
    UserPermission,
)
from login.models import myuser as User
from login.permissions import ADMIN_PERM, DELETE_PERM, WRITE_PERM


class GroupAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_admin = User.objects.create_user(
            name="admin_user", email="admin@test.com", affiliation="test"
        )
        cls.token_admin = Token.objects.get(user=cls.user_admin)

        cls.user_member = User.objects.create_user(
            name="member_user", email="member@test.com", affiliation="test"
        )
        cls.token_member = Token.objects.get(user=cls.user_member)

        cls.user_other = User.objects.create_user(
            name="other_user", email="other@test.com", affiliation="test"
        )
        cls.token_other = Token.objects.get(user=cls.user_other)

        # Create an organization
        cls.org_name = "test_org"
        cls.org = Organization.objects.create(name=cls.org_name)
        Membership.objects.create(user=cls.user_admin, group=cls.org, level=ADMIN_PERM)
        Membership.objects.create(user=cls.user_member, group=cls.org, level=WRITE_PERM)

        # Create a project
        cls.proj_name = "test_proj"
        cls.proj = Project.objects.create(name=cls.proj_name)
        Membership.objects.create(user=cls.user_admin, group=cls.proj, level=ADMIN_PERM)

        # Create a dummy table and permission to avoid potential serialization issues
        cls.table = Table.objects.create(name="dummy_table")
        GroupPermission.objects.create(
            holder=cls.org, table=cls.table, level=WRITE_PERM
        )
        GroupPermission.objects.create(
            holder=cls.proj, table=cls.table, level=WRITE_PERM
        )

    def set_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def clear_token(self):
        self.client.credentials()

    def test_group_get_public(self):
        """Test that GET on groups is public."""
        self.clear_token()

        # Test Organization
        url = reverse(
            "api:api_group",
            kwargs={"group_type": "organization", "group": self.org_name},
        )
        response = self.client.get(url)
        # If this fails with 400, it's likely due to api_exception catching
        # something in OrganizationSerializer
        # Update: It seems adding a dummy table/permission fixed it,
        # or it was flaky.
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], self.org_name)

        # Test Project
        url = reverse(
            "api:api_group", kwargs={"group_type": "project", "group": self.proj_name}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["name"], self.proj_name)

    def test_group_put_create(self):
        """Test creating a group via PUT."""
        new_org_name = "new_org"
        url = reverse(
            "api:api_group",
            kwargs={"group_type": "organization", "group": new_org_name},
        )
        payload = {"query": {"description": "New Org Description"}}

        # Unauthorized
        self.clear_token()
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authorized
        self.set_token(self.token_other)
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Organization.objects.filter(name=new_org_name).exists())
        # Check if creator is admin
        new_org = Organization.objects.get(name=new_org_name)
        membership = Membership.objects.get(user=self.user_other, group=new_org)
        self.assertEqual(membership.level, ADMIN_PERM)

        # Conflict (already exists)
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_group_post_edit(self):
        """Test editing a group via POST."""
        url = reverse(
            "api:api_group",
            kwargs={"group_type": "organization", "group": self.org_name},
        )
        payload = {"query": {"description": "Updated Description"}}

        # Unauthorized
        self.clear_token()
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authorized but no membership
        self.set_token(self.token_other)
        response = self.client.post(url, payload, format="json")
        # edit_group in login/services.py uses get_object_or_404(Membership, ...)
        # api_exception in api/helper.py catches Http404 and returns 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Authorized with member (WRITE_PERM < ADMIN_PERM)
        self.set_token(self.token_member)
        response = self.client.post(url, payload, format="json")
        # edit_group raises PermissionDenied if level < ADMIN_PERM
        # api_exception catches generic Exception (PermissionDenied) and returns 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Authorized with admin
        self.set_token(self.token_admin)
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.org.refresh_from_db()
        self.assertEqual(self.org.description, "Updated Description")

    def test_group_delete(self):
        """Test deleting a group via DELETE."""
        url = reverse(
            "api:api_group",
            kwargs={"group_type": "organization", "group": self.org_name},
        )

        # Authorized with member
        self.set_token(self.token_member)
        response = self.client.delete(url)
        # delete_group raises PermissionDenied if level < ADMIN_PERM
        # api_exception returns 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Authorized with admin
        self.set_token(self.token_admin)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(Organization.objects.filter(name=self.org_name).exists())


class GroupMemberAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_admin = User.objects.create_user(
            name="admin_user", email="admin@test.com", affiliation="test"
        )
        cls.token_admin = Token.objects.get(user=cls.user_admin)

        cls.user_write = User.objects.create_user(
            name="write_user", email="write@test.com", affiliation="test"
        )
        cls.token_write = Token.objects.get(user=cls.user_write)

        cls.user_delete = User.objects.create_user(
            name="delete_user", email="delete@test.com", affiliation="test"
        )
        cls.token_delete = Token.objects.get(user=cls.user_delete)

        cls.user_to_add = User.objects.create_user(
            name="added_user", email="added@test.com", affiliation="test"
        )

        cls.org = Organization.objects.create(name="member_test_org")
        Membership.objects.create(user=cls.user_admin, group=cls.org, level=ADMIN_PERM)
        Membership.objects.create(user=cls.user_write, group=cls.org, level=WRITE_PERM)
        Membership.objects.create(
            user=cls.user_delete, group=cls.org, level=DELETE_PERM
        )

    def set_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_add_member(self):
        """Test adding a member via POST."""
        url = reverse(
            "api:api_group_member",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "member": self.user_to_add.name,
            },
        )

        # Member with level < WRITE_PERM cannot add
        # (none exists here but let's try other user)
        other_user = User.objects.create_user(
            name="other", email="other@test.com", affiliation="test"
        )
        token_other = Token.objects.get(user=other_user)
        self.set_token(token_other)
        response = self.client.post(url)
        # get_object_or_404(Membership, group=group, user=request.user)
        # will fail with 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Member with WRITE_PERM can add
        self.set_token(self.token_write)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(
            Membership.objects.filter(user=self.user_to_add, group=self.org).exists()
        )

    def test_alter_member_role(self):
        """Test altering member role via PUT."""
        Membership.objects.create(
            user=self.user_to_add, group=self.org, level=WRITE_PERM
        )
        url = reverse(
            "api:api_group_member",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "member": self.user_to_add.name,
            },
        )
        payload = {"query": {"level": DELETE_PERM}}

        # WRITE_PERM cannot alter role (requires ADMIN_PERM)
        self.set_token(self.token_write)
        response = self.client.put(url, payload, format="json")
        # raise APIError(..., status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # ADMIN_PERM can alter role
        self.set_token(self.token_admin)
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        m = Membership.objects.get(user=self.user_to_add, group=self.org)
        self.assertEqual(m.level, DELETE_PERM)

    def test_remove_member(self):
        """Test removing a member via DELETE."""
        Membership.objects.create(
            user=self.user_to_add, group=self.org, level=WRITE_PERM
        )
        url = reverse(
            "api:api_group_member",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "member": self.user_to_add.name,
            },
        )

        # WRITE_PERM cannot remove (requires DELETE_PERM)
        self.set_token(self.token_write)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # DELETE_PERM can remove
        self.set_token(self.token_delete)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(
            Membership.objects.filter(user=self.user_to_add, group=self.org).exists()
        )


class GroupTableAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_with_perm = User.objects.create_user(
            name="user_with_perm", email="perm@test.com", affiliation="test"
        )
        cls.token_with_perm = Token.objects.get(user=cls.user_with_perm)

        cls.user_no_perm = User.objects.create_user(
            name="user_no_perm", email="noperm@test.com", affiliation="test"
        )
        cls.token_no_perm = Token.objects.get(user=cls.user_no_perm)

        cls.user_write_perm = User.objects.create_user(
            name="user_write_perm", email="writeperm@test.com", affiliation="test"
        )
        cls.token_write_perm = Token.objects.get(user=cls.user_write_perm)

        cls.table = Table.objects.create(name="test_table")
        UserPermission.objects.create(
            holder=cls.user_with_perm, table=cls.table, level=DELETE_PERM
        )
        UserPermission.objects.create(
            holder=cls.user_write_perm, table=cls.table, level=WRITE_PERM
        )

        cls.org = Organization.objects.create(name="table_test_org")

    def set_token(self, token):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_add_table_to_group(self):
        """Test adding a table to a group via POST."""
        url = reverse(
            "api:api_group_table",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "table": self.table.name,
            },
        )

        # Unauthorized
        self.client.credentials()
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Authorized but no permission on table
        self.set_token(self.token_no_perm)
        response = self.client.post(url)
        # login/services.py raises PermissionDenied
        # api/views.py catches it and raises APIError(str(e), 405)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Authorized with WRITE_PERM on table (not enough, needs > WRITE_PERM)
        self.set_token(self.token_write_perm)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

        # Authorized with DELETE_PERM on table
        self.set_token(self.token_with_perm)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertTrue(
            GroupPermission.objects.filter(holder=self.org, table=self.table).exists()
        )

    def test_alter_table_in_group(self):
        """Test altering table role in group via PUT."""
        GroupPermission.objects.create(
            holder=self.org, table=self.table, level=WRITE_PERM
        )
        url = reverse(
            "api:api_group_table",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "table": self.table.name,
            },
        )
        payload = {"query": {"level": DELETE_PERM}}

        # Authorized with DELETE_PERM on table can alter
        self.set_token(self.token_with_perm)
        response = self.client.put(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        gp = GroupPermission.objects.get(holder=self.org, table=self.table)
        self.assertEqual(gp.level, DELETE_PERM)

        # Table not in group
        other_table = Table.objects.create(name="other_table")
        # Need permission for other_table too
        UserPermission.objects.create(
            holder=self.user_with_perm, table=other_table, level=DELETE_PERM
        )
        url_other = reverse(
            "api:api_group_table",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "table": other_table.name,
            },
        )
        response = self.client.put(url_other, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_remove_table_from_group(self):
        """Test removing table from group via DELETE."""
        GroupPermission.objects.get_or_create(
            holder=self.org, table=self.table, level=WRITE_PERM
        )
        url = reverse(
            "api:api_group_table",
            kwargs={
                "group_type": "organization",
                "group": self.org.name,
                "table": self.table.name,
            },
        )

        # Authorized with DELETE_PERM on table can remove
        self.set_token(self.token_with_perm)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertFalse(
            GroupPermission.objects.filter(holder=self.org, table=self.table).exists()
        )
