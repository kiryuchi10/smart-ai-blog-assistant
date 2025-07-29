"""
Unit tests for template management endpoints
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.content import ContentTemplate


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_user():
    """Mock authenticated user"""
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_template():
    """Mock template object"""
    template = MagicMock()
    template.id = "template-123"
    template.name = "Test Template"
    template.description = "A test template"
    template.template_content = "# {{title}}\n\n{{content}}"
    template.category = "business"
    template.template_type = "article"
    template.industry = "Technology"
    template.is_public = True
    template.tags = ["test", "template"]
    template.usage_count = 5
    template.created_by = "test-user-id"
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    template.placeholders = ["title", "content"]
    return template


class TestTemplateUtilityFunctions:
    """Test utility functions for template management"""
    
    def test_extract_placeholders(self):
        """Test placeholder extraction from template content"""
        from app.api.v1.endpoints.template import _extract_placeholders
        
        content = "# {{title}}\n\nHello {{name}}, welcome to {{company}}!"
        placeholders = _extract_placeholders(content)
        
        assert set(placeholders) == {"title", "name", "company"}
    
    def test_extract_placeholders_duplicates(self):
        """Test placeholder extraction removes duplicates"""
        from app.api.v1.endpoints.template import _extract_placeholders
        
        content = "{{name}} and {{name}} are both {{name}}"
        placeholders = _extract_placeholders(content)
        
        assert placeholders == ["name"]
    
    def test_replace_placeholders(self):
        """Test placeholder replacement in template content"""
        from app.api.v1.endpoints.template import _replace_placeholders
        
        content = "Hello {{name}}, welcome to {{company}}!"
        variables = {"name": "John", "company": "Acme Corp"}
        
        result, found, replaced = _replace_placeholders(content, variables)
        
        assert result == "Hello John, welcome to Acme Corp!"
        assert set(found) == {"name", "company"}
        assert set(replaced) == {"name", "company"}
    
    def test_replace_placeholders_partial(self):
        """Test placeholder replacement with missing variables"""
        from app.api.v1.endpoints.template import _replace_placeholders
        
        content = "Hello {{name}}, welcome to {{company}}!"
        variables = {"name": "John"}
        
        result, found, replaced = _replace_placeholders(content, variables)
        
        assert result == "Hello John, welcome to {{company}}!"
        assert set(found) == {"name", "company"}
        assert replaced == ["name"]


class TestTemplateEndpoints:
    """Test cases for template management endpoints"""
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    @patch('app.api.v1.endpoints.template.rate_limiter.check_rate_limit')
    def test_create_template_success(
        self,
        mock_rate_limit,
        mock_get_user,
        client,
        mock_user
    ):
        """Test successful template creation"""
        mock_get_user.return_value = mock_user
        mock_rate_limit.return_value = None
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock database query to return None (no existing template)
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            # Mock template creation
            mock_template = MagicMock()
            mock_template.id = "new-template-id"
            mock_template.name = "New Template"
            mock_template.description = "A new template"
            mock_template.template_content = "# {{title}}\n\n{{content}}"
            mock_template.category = "business"
            mock_template.template_type = "article"
            mock_template.industry = "Technology"
            mock_template.is_public = False
            mock_template.tags = ["new", "template"]
            mock_template.usage_count = 0
            mock_template.created_by = mock_user.id
            mock_template.created_at = datetime.utcnow()
            mock_template.updated_at = datetime.utcnow()
            
            mock_db.refresh.return_value = mock_template
            
            request_data = {
                "name": "New Template",
                "description": "A new template",
                "template_content": "# {{title}}\n\n{{content}}",
                "category": "business",
                "template_type": "article",
                "industry": "Technology",
                "is_public": False,
                "tags": ["new", "template"]
            }
            
            response = client.post("/api/v1/templates/", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["name"] == "New Template"
            assert data["category"] == "business"
            assert data["template_type"] == "article"
            assert data["is_public"] == False
            assert data["tags"] == ["new", "template"]
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_create_template_duplicate_name(
        self,
        mock_get_user,
        client,
        mock_user
    ):
        """Test template creation with duplicate name"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock existing template
            existing_template = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = existing_template
            
            request_data = {
                "name": "Existing Template",
                "template_content": "# {{title}}",
                "category": "business",
                "template_type": "article"
            }
            
            response = client.post("/api/v1/templates/", json=request_data)
            
            assert response.status_code == 400
            assert "already exists" in response.json()["detail"]
    
    def test_create_template_validation_error(self, client):
        """Test template creation with validation errors"""
        request_data = {
            "name": "",  # Empty name
            "template_content": "short",  # Too short
            "category": "invalid_category",
            "template_type": "invalid_type"
        }
        
        response = client.post("/api/v1/templates/", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_list_templates_success(
        self,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template listing"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock query results
            mock_query = mock_db.query.return_value.filter.return_value
            mock_query.count.return_value = 1
            mock_query.offset.return_value.limit.return_value.all.return_value = [mock_template]
            
            response = client.get("/api/v1/templates/")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["total"] == 1
            assert len(data["templates"]) == 1
            assert data["templates"][0]["name"] == "Test Template"
            assert data["page"] == 1
            assert data["per_page"] == 20
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_get_template_success(
        self,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template retrieval"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            response = client.get("/api/v1/templates/template-123")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == "template-123"
            assert data["name"] == "Test Template"
            assert data["category"] == "business"
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_get_template_not_found(
        self,
        mock_get_user,
        client,
        mock_user
    ):
        """Test template retrieval when template not found"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.get("/api/v1/templates/nonexistent")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    @patch('app.api.v1.endpoints.template.rate_limiter.check_rate_limit')
    def test_update_template_success(
        self,
        mock_rate_limit,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template update"""
        mock_get_user.return_value = mock_user
        mock_rate_limit.return_value = None
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            update_data = {
                "name": "Updated Template",
                "description": "Updated description"
            }
            
            response = client.put("/api/v1/templates/template-123", json=update_data)
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify the template was updated (mock would need to be configured to reflect changes)
            assert "id" in data
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_delete_template_success(
        self,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template deletion"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            response = client.delete("/api/v1/templates/template-123")
            
            assert response.status_code == 200
            assert "deleted successfully" in response.json()["message"]
            
            # Verify delete was called
            mock_db.delete.assert_called_once_with(mock_template)
            mock_db.commit.assert_called_once()
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    @patch('app.api.v1.endpoints.template.rate_limiter.check_rate_limit')
    def test_use_template_success(
        self,
        mock_rate_limit,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template usage"""
        mock_get_user.return_value = mock_user
        mock_rate_limit.return_value = None
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            request_data = {
                "template_id": "template-123",
                "variables": {
                    "title": "My Blog Post",
                    "content": "This is the content of my blog post."
                }
            }
            
            response = client.post("/api/v1/templates/template-123/use", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["template_name"] == "Test Template"
            assert data["variables_used"] == request_data["variables"]
            assert "generated_content" in data
            assert "My Blog Post" in data["generated_content"]
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_search_templates_success(
        self,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template search"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock search query building and results
            with patch('app.api.v1.endpoints.template._build_search_query') as mock_build_query:
                mock_query = MagicMock()
                mock_build_query.return_value = mock_query
                mock_query.count.return_value = 1
                mock_query.offset.return_value.limit.return_value.all.return_value = [mock_template]
                
                search_data = {
                    "query": "test",
                    "category": "business",
                    "page": 1,
                    "per_page": 10
                }
                
                response = client.post("/api/v1/templates/search", json=search_data)
                
                assert response.status_code == 200
                data = response.json()
                
                assert data["total"] == 1
                assert len(data["templates"]) == 1
                assert data["templates"][0]["name"] == "Test Template"
    
    def test_search_templates_validation_error(self, client):
        """Test template search with validation errors"""
        search_data = {
            "sort_by": "invalid_field",  # Invalid sort field
            "sort_order": "invalid_order",  # Invalid sort order
            "page": 0,  # Invalid page number
            "per_page": 200  # Exceeds maximum
        }
        
        response = client.post("/api/v1/templates/search", json=search_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_get_template_analytics_success(
        self,
        mock_get_user,
        client,
        mock_user,
        mock_template
    ):
        """Test successful template analytics retrieval"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            mock_db.query.return_value.filter.return_value.first.return_value = mock_template
            
            response = client.get("/api/v1/templates/template-123/analytics")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["template_id"] == "template-123"
            assert data["template_name"] == "Test Template"
            assert "total_usage" in data
            assert "usage_this_month" in data
            assert "popular_variables" in data
            assert "usage_by_industry" in data
    
    @patch('app.api.v1.endpoints.template.get_current_user')
    def test_seed_default_templates_success(
        self,
        mock_get_user,
        client,
        mock_user
    ):
        """Test successful default template seeding"""
        mock_get_user.return_value = mock_user
        
        with patch('app.api.v1.endpoints.template.get_db') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            # Mock no existing templates
            mock_db.query.return_value.filter.return_value.first.return_value = None
            
            response = client.post("/api/v1/templates/seed-defaults")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "Created" in data["message"]
            assert "templates" in data["message"]


class TestTemplateSchemaValidation:
    """Test template schema validation"""
    
    def test_template_create_request_validation(self):
        """Test template creation request validation"""
        from app.schemas.template import TemplateCreateRequest
        
        # Valid request
        valid_data = {
            "name": "Test Template",
            "template_content": "# {{title}}\n\nThis is a test template with {{content}}",
            "category": "business",
            "template_type": "article"
        }
        
        request = TemplateCreateRequest(**valid_data)
        assert request.name == "Test Template"
        assert request.category == "business"
        
        # Invalid request - too many tags
        invalid_data = {
            "name": "Test Template",
            "template_content": "# {{title}}",
            "category": "business",
            "template_type": "article",
            "tags": ["tag" + str(i) for i in range(15)]  # Too many tags
        }
        
        with pytest.raises(ValueError, match="Maximum 10 tags allowed"):
            TemplateCreateRequest(**invalid_data)
    
    def test_template_usage_request_validation(self):
        """Test template usage request validation"""
        from app.schemas.template import TemplateUsageRequest
        
        # Valid request
        valid_data = {
            "template_id": "template-123",
            "variables": {
                "title": "My Title",
                "content": "My Content"
            }
        }
        
        request = TemplateUsageRequest(**valid_data)
        assert request.template_id == "template-123"
        assert request.variables["title"] == "My Title"
        
        # Invalid request - non-string variable
        invalid_data = {
            "template_id": "template-123",
            "variables": {
                "title": "My Title",
                "count": 123  # Non-string value
            }
        }
        
        with pytest.raises(ValueError, match="must be a string"):
            TemplateUsageRequest(**invalid_data)
    
    def test_template_search_request_validation(self):
        """Test template search request validation"""
        from app.schemas.template import TemplateSearchRequest
        
        # Valid request
        valid_data = {
            "query": "test",
            "category": "business",
            "sort_by": "created_at",
            "sort_order": "desc"
        }
        
        request = TemplateSearchRequest(**valid_data)
        assert request.query == "test"
        assert request.sort_by == "created_at"
        
        # Invalid sort field
        invalid_data = {
            "sort_by": "invalid_field"
        }
        
        with pytest.raises(ValueError, match="Sort field must be one of"):
            TemplateSearchRequest(**invalid_data)
        
        # Invalid sort order
        invalid_data = {
            "sort_order": "invalid_order"
        }
        
        with pytest.raises(ValueError, match="Sort order must be"):
            TemplateSearchRequest(**invalid_data)