"""
Tests for leads API endpoints
"""
import pytest
from io import BytesIO


class TestLeads:
    """Test leads management API"""

    def test_create_lead_success(self, authorized_client, db, test_user):
        """Test creating a new lead"""
        response = authorized_client.post("/api/v1/leads/", json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "1234567890",
            "company": "Jane's Company",
            "title": "Manager",
            "tags": "hot,enterprise"
        })

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Jane Doe"
        assert data["email"] == "jane@example.com"
        assert data["user_id"] == test_user.id
        assert data["status"] == "new"

    def test_create_lead_quota_exceeded(self, authorized_client, test_user):
        """Test creating lead when quota exceeded"""
        test_user.leads_used = test_user.leads_quota

        response = authorized_client.post("/api/v1/leads/", json={
            "name": "Jane Doe",
            "email": "jane@example.com"
        })

        assert response.status_code == 403
        assert "quota" in response.json()["detail"].lower()

    def test_list_leads(self, authorized_client, multiple_leads):
        """Test listing all leads"""
        response = authorized_client.get("/api/v1/leads/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(multiple_leads)

    def test_list_leads_with_status_filter(self, authorized_client, multiple_leads):
        """Test listing leads with status filter"""
        response = authorized_client.get("/api/v1/leads/?status=new")

        assert response.status_code == 200
        data = response.json()
        assert all(lead["status"] == "new" for lead in data)

    def test_list_leads_with_search(self, authorized_client, test_lead):
        """Test searching leads"""
        response = authorized_client.get(f"/api/v1/leads/?search={test_lead.name}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert any(lead["name"] == test_lead.name for lead in data)

    def test_get_lead_detail(self, authorized_client, test_lead):
        """Test getting single lead details"""
        response = authorized_client.get(f"/api/v1/leads/{test_lead.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_lead.id
        assert data["name"] == test_lead.name

    def test_get_lead_not_found(self, authorized_client):
        """Test getting non-existent lead"""
        response = authorized_client.get("/api/v1/leads/99999")

        assert response.status_code == 404

    def test_update_lead(self, authorized_client, test_lead):
        """Test updating a lead"""
        response = authorized_client.put(f"/api/v1/leads/{test_lead.id}", json={
            "name": "Updated Name",
            "status": "contacted"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["status"] == "contacted"

    def test_delete_lead(self, authorized_client, test_lead, test_user):
        """Test deleting a lead"""
        initial_used = test_user.leads_used

        response = authorized_client.delete(f"/api/v1/leads/{test_lead.id}")

        assert response.status_code == 200

        # Verify lead is deleted
        get_response = authorized_client.get(f"/api/v1/leads/{test_lead.id}")
        assert get_response.status_code == 404

    def test_delete_lead_not_found(self, authorized_client):
        """Test deleting non-existent lead"""
        response = authorized_client.delete("/api/v1/leads/99999")

        assert response.status_code == 404

    def test_import_leads_csv(self, authorized_client):
        """Test importing leads from CSV"""
        csv_content = "name,email,company,title\nJohn Doe,john@example.com,Acme,CEO\nJane Doe,jane@example.com,Corp,CTO"
        file = BytesIO(csv_content.encode())

        response = authorized_client.post(
            "/api/v1/leads/import",
            files={"file": ("leads.csv", file, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 2
        assert data["failed"] == 0

    def test_import_leads_invalid_file(self, authorized_client):
        """Test importing with invalid file format"""
        file = BytesIO(b"invalid content")

        response = authorized_client.post(
            "/api/v1/leads/import",
            files={"file": ("leads.txt", file, "text/plain")}
        )

        assert response.status_code == 400

    def test_dashboard_stats(self, authorized_client, multiple_leads, test_user):
        """Test getting dashboard statistics"""
        response = authorized_client.get("/api/v1/leads/stats/dashboard")

        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == len(multiple_leads)
        assert "quota" in data
        assert "status_distribution" in data
        assert data["plan"] == test_user.plan

    def test_unauthorized_access(self, client):
        """Test accessing leads without authentication"""
        response = client.get("/api/v1/leads/")
        assert response.status_code == 403

        response = client.post("/api/v1/leads/", json={"name": "Test"})
        assert response.status_code == 403
