"""
File and folder parsing service for extracting content
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Any
import markdown
from PIL import Image

class FileParser:
    def __init__(self):
        self.supported_formats = ['.md', '.txt', '.html']
        self.image_formats = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    def parse_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        Parse folder contents and extract structured data
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        result = {
            'title': self._extract_title_from_folder(folder_path),
            'content': '',
            'images': [],
            'metadata': {},
            'raw_files': []
        }
        
        # Process all files in folder
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in self.supported_formats:
                    content = self._parse_text_file(file_path)
                    result['content'] += content + '\n\n'
                    result['raw_files'].append(str(file_path))
                
                elif file_path.suffix.lower() in self.image_formats:
                    image_info = self._parse_image_file(file_path)
                    result['images'].append(image_info)
        
        # Extract metadata from content
        result['metadata'] = self._extract_metadata(result['content'])
        
        return result
    
    def _extract_title_from_folder(self, folder_path: Path) -> str:
        """
        Extract title from folder name or README file
        """
        # Try to find title in README or index files
        for readme_file in ['README.md', 'readme.md', 'index.md', 'INDEX.md']:
            readme_path = folder_path / readme_file
            if readme_path.exists():
                content = readme_path.read_text(encoding='utf-8')
                title = self._extract_title_from_content(content)
                if title:
                    return title
        
        # Fallback to folder name
        return folder_path.name.replace('-', ' ').replace('_', ' ').title()
    
    def _parse_text_file(self, file_path: Path) -> str:
        """
        Parse text-based files and return content
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            if file_path.suffix.lower() == '.md':
                # Convert markdown to HTML for processing
                html_content = markdown.markdown(content)
                return content  # Return original markdown
            
            return content
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            return ""
    
    def _parse_image_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Parse image files and extract metadata
        """
        try:
            with Image.open(file_path) as img:
                return {
                    'path': str(file_path),
                    'filename': file_path.name,
                    'size': img.size,
                    'format': img.format,
                    'mode': img.mode
                }
        except Exception as e:
            return {
                'path': str(file_path),
                'filename': file_path.name,
                'error': str(e)
            }
    
    def _extract_title_from_content(self, content: str) -> str:
        """
        Extract title from content using various patterns
        """
        # Try to find markdown h1
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()
        
        # Try to find HTML h1
        html_h1_match = re.search(r'<h1[^>]*>(.+?)</h1>', content, re.IGNORECASE)
        if html_h1_match:
            return html_h1_match.group(1).strip()
        
        # Try to find title in first line
        lines = content.strip().split('\n')
        if lines:
            first_line = lines[0].strip()
            if len(first_line) < 100 and not first_line.startswith(('http', 'www')):
                return first_line
        
        return ""
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """
        Extract metadata from content (tags, categories, etc.)
        """
        metadata = {
            'tags': [],
            'categories': [],
            'word_count': len(content.split()),
            'reading_time': max(1, len(content.split()) // 200)  # Assume 200 WPM
        }
        
        # Extract hashtags as tags
        hashtags = re.findall(r'#(\w+)', content)
        metadata['tags'] = list(set(hashtags))
        
        # Extract categories from folder structure or content
        category_patterns = [
            r'category:\s*(.+)',
            r'categories:\s*(.+)',
            r'\[category\](.+)\[/category\]'
        ]
        
        for pattern in category_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                categories = [cat.strip() for cat in matches[0].split(',')]
                metadata['categories'].extend(categories)
        
        return metadata
    
    def validate_folder_structure(self, folder_path: str) -> Dict[str, Any]:
        """
        Validate folder structure and return status
        """
        folder_path = Path(folder_path)
        
        validation = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'file_count': 0,
            'has_content': False,
            'has_images': False
        }
        
        if not folder_path.exists():
            validation['valid'] = False
            validation['errors'].append("Folder does not exist")
            return validation
        
        files = list(folder_path.rglob('*'))
        validation['file_count'] = len([f for f in files if f.is_file()])
        
        # Check for content files
        content_files = [f for f in files if f.suffix.lower() in self.supported_formats]
        validation['has_content'] = len(content_files) > 0
        
        # Check for images
        image_files = [f for f in files if f.suffix.lower() in self.image_formats]
        validation['has_images'] = len(image_files) > 0
        
        if not validation['has_content']:
            validation['warnings'].append("No supported content files found")
        
        if validation['file_count'] == 0:
            validation['valid'] = False
            validation['errors'].append("Folder is empty")
        
        return validation