# Folder-Based Auto-Publishing System

This directory contains the folder monitoring system for automatic content processing and publishing.

## Directory Structure

- **folders/**: Drop new content folders here for automatic processing
- **published/**: Successfully processed folders are moved here
- **failed/**: Folders that failed processing are moved here with error logs

## How to Use

1. Create a new folder in the `folders/` directory
2. Add your content files:
   - `content.md` or `README.md` - Main content file
   - `metadata.json` - Optional metadata (title, tags, etc.)
   - Images and other assets
3. The system will automatically:
   - Detect the new folder
   - Parse and extract content
   - Enhance content with AI
   - Publish to configured platforms (if enabled)
   - Move folder to `published/` or `failed/`

## Folder Structure Example

```
my-blog-post/
├── content.md          # Main blog content
├── metadata.json       # Post metadata
├── images/
│   ├── hero.jpg       # Hero image
│   └── chart.png      # Supporting images
└── assets/
    └── data.csv       # Additional data files
```

## Metadata Format

```json
{
  "title": "My Blog Post Title",
  "description": "Brief description of the post",
  "tags": ["technology", "ai", "automation"],
  "category": "tutorial",
  "author": "Your Name",
  "publish_immediately": true,
  "platforms": ["wordpress", "medium"],
  "scheduled_time": "2025-01-28T15:00:00Z"
}
```

## Supported File Types

- **Content**: `.md`, `.txt`, `.docx`, `.pdf`
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`
- **Data**: `.csv`, `.json`, `.xlsx`

## Processing Status

Check the system logs or dashboard to monitor processing status:
- **Pending**: Folder detected, processing started
- **Processing**: Content extraction and AI enhancement in progress
- **Publishing**: Content being published to platforms
- **Completed**: Successfully processed and published
- **Failed**: Processing failed (check error.log in failed folder)

## Troubleshooting

If a folder fails processing:
1. Check the `error.log` file in the failed folder
2. Verify file formats and content structure
3. Ensure metadata.json is valid JSON
4. Check system logs for detailed error information

## Configuration

Folder monitoring can be configured via environment variables:
- `MONITORED_FOLDERS_PATH`: Path to monitor for new folders
- `AUTO_PUBLISH_ENABLED`: Enable/disable automatic publishing
- `PUBLISHING_RETRY_ATTEMPTS`: Number of retry attempts for failed publishing