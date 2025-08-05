"""
Multi-platform publishing service (WordPress, Medium, Ghost, etc.)
"""
import requests
import base64
from typing import Dict, Any, Optional
from app.config import settings

class Publisher:
    def __init__(self):
        self.wordpress_config = {
            'url': settings.WORDPRESS_URL,
            'username': settings.WORDPRESS_USERNAME,
            'password': settings.WORDPRESS_APP_PASSWORD
        }
    
    def publish_to_wordpress(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish post to WordPress using REST API
        """
        if not all([self.wordpress_config['url'], 
                   self.wordpress_config['username'], 
                   self.wordpress_config['password']]):
            raise Exception("WordPress configuration incomplete")
        
        # Prepare WordPress API endpoint
        api_url = f"{self.wordpress_config['url'].rstrip('/')}/wp-json/wp/v2/posts"
        
        # Prepare authentication
        credentials = f"{self.wordpress_config['username']}:{self.wordpress_config['password']}"
        token = base64.b64encode(credentials.encode()).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare post payload
        payload = {
            'title': post_data.get('title', 'Untitled Post'),
            'content': post_data.get('content', ''),
            'status': post_data.get('status', 'draft'),  # draft, publish
            'excerpt': post_data.get('excerpt', ''),
            'categories': post_data.get('categories', []),
            'tags': post_data.get('tags', []),
            'meta': {
                'description': post_data.get('meta_description', '')
            }
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return {
                'success': True,
                'post_id': result.get('id'),
                'url': result.get('link'),
                'status': result.get('status'),
                'message': 'Post published successfully to WordPress'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to publish to WordPress'
            }
    
    def publish_to_medium(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish post to Medium (placeholder for future implementation)
        """
        # Medium API implementation would go here
        return {
            'success': False,
            'message': 'Medium publishing not yet implemented'
        }
    
    def publish_to_ghost(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish post to Ghost (placeholder for future implementation)
        """
        # Ghost API implementation would go here
        return {
            'success': False,
            'message': 'Ghost publishing not yet implemented'
        }
    
    def publish_to_platform(self, platform: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish to specified platform
        """
        publishers = {
            'wordpress': self.publish_to_wordpress,
            'medium': self.publish_to_medium,
            'ghost': self.publish_to_ghost
        }
        
        if platform not in publishers:
            return {
                'success': False,
                'error': f'Unsupported platform: {platform}',
                'message': f'Platform {platform} is not supported'
            }
        
        return publishers[platform](post_data)
    
    def format_content_for_platform(self, content: str, platform: str) -> str:
        """
        Format content for specific platform requirements
        """
        if platform == 'wordpress':
            # WordPress supports HTML and markdown
            return content
        
        elif platform == 'medium':
            # Medium prefers clean markdown
            return self._clean_markdown(content)
        
        elif platform == 'ghost':
            # Ghost supports markdown and HTML
            return content
        
        return content
    
    def _clean_markdown(self, content: str) -> str:
        """
        Clean markdown for platforms that prefer simpler formatting
        """
        # Remove complex HTML tags, keep basic markdown
        import re
        
        # Remove HTML comments
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # Remove complex HTML tags, keep basic ones
        allowed_tags = ['strong', 'em', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        # This is a simplified approach - in production, use a proper HTML sanitizer
        
        return content
    
    def validate_post_data(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate post data before publishing
        """
        validation = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Required fields
        if not post_data.get('title'):
            validation['valid'] = False
            validation['errors'].append('Title is required')
        
        if not post_data.get('content'):
            validation['valid'] = False
            validation['errors'].append('Content is required')
        
        # Warnings for best practices
        if len(post_data.get('title', '')) > 60:
            validation['warnings'].append('Title is longer than 60 characters (SEO recommendation)')
        
        if not post_data.get('meta_description'):
            validation['warnings'].append('Meta description is missing (SEO recommendation)')
        
        if not post_data.get('tags'):
            validation['warnings'].append('No tags specified (SEO recommendation)')
        
        return validation
    
    def schedule_post(self, post_data: Dict[str, Any], publish_time: str) -> Dict[str, Any]:
        """
        Schedule post for future publication (placeholder)
        """
        # This would integrate with a job scheduler like Celery
        return {
            'success': False,
            'message': 'Post scheduling not yet implemented'
        }