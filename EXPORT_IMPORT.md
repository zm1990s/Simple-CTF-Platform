# Competition Export/Import Feature

## Overview

The CTF platform now supports exporting and importing competitions and challenges, enabling easy cross-platform migration and backup capabilities.

## Features

### 1. Competition Export
- Export single competitions with all associated challenges as JSON
- Export all competitions at once as a ZIP file
- Includes competition metadata and all challenge details
- Files can be easily shared between different platform instances

### 2. Challenge Export
- Export individual challenges as JSON files
- Useful for creating challenge libraries or sharing specific challenges

### 3. Competition Import
- Import competitions from exported JSON files
- Automatically creates competition and all challenges
- Imported competitions start in "draft" status for safety

## Usage

### Exporting a Single Competition

1. Navigate to **Admin** → **Manage Competitions**
2. Find the competition you want to export
3. Click the **Export** button (download icon) for that competition
4. A JSON file will be downloaded with the format: `competition_name_export_YYYYMMDD_HHMMSS.json`

### Exporting All Competitions

1. Navigate to **Admin** → **Manage Competitions**
2. Click the **Export All** button in the top right
3. A ZIP file containing all competitions will be downloaded
4. Each competition is saved as a separate JSON file within the ZIP

### Exporting a Single Challenge

1. Navigate to **Admin** → **Manage Challenges**
2. Find the challenge you want to export
3. Click the **Export** button (download icon)
4. A JSON file will be downloaded with the format: `challenge_title_export_YYYYMMDD_HHMMSS.json`

### Importing a Competition

1. Navigate to **Admin** → **Manage Competitions**
2. Click the **Import** button in the top right
3. Click **Select JSON File** and choose your exported competition JSON file
4. Click **Import**
5. The competition and all its challenges will be created in draft status

## Export File Format

### Competition Export Structure

```json
{
  "name": "Competition Name",
  "description": "Competition description",
  "countdown_minutes": 60,
  "export_date": "2024-01-15T10:30:00",
  "challenges": [
    {
      "title": "Challenge 1",
      "description": "Challenge description",
      "points": 100,
      "category": "Web",
      "is_active": true
    }
  ]
}
```

### Challenge Export Structure

```json
{
  "title": "Challenge Title",
  "description": "Challenge description",
  "points": 100,
  "category": "Web",
  "is_active": true,
  "competition_name": "Original Competition",
  "export_date": "2024-01-15T10:30:00"
}
```

## Use Cases

### 1. Platform Migration
Export competitions from one CTF platform instance and import them to another:
- Development → Production migration
- Server migration or backup
- Creating separate environments (training, competition, etc.)

### 2. Competition Backup
- Regularly export competitions to create backups
- Archive completed competitions
- Preserve competition templates for future use

### 3. Sharing Challenges
- Export individual challenges to share with other CTF organizers
- Create a library of reusable challenges
- Distribute challenge sets to multiple platforms

### 4. Competition Templates
- Export well-designed competitions as templates
- Reuse competition structures with different challenges
- Quickly set up similar competitions

## Important Notes

### Limitations

1. **Files Not Included**: Basic JSON exports do not include challenge description images or attached files. Only metadata is exported.

2. **Draft Status**: Imported competitions are created in "draft" status. You must manually start them when ready.

3. **No Submissions**: Exported competitions do not include submission history. Only the competition structure is preserved.

4. **IDs Will Change**: Imported competitions and challenges receive new database IDs on the target platform.

### Best Practices

1. **Test Imports**: Always test imported competitions in draft mode before starting them.

2. **Verify Content**: After importing, review all challenges to ensure content is correct.

3. **Handle Files Manually**: If challenges have description images or files, you'll need to upload them manually after import.

4. **Name Conflicts**: If importing a competition with the same name as an existing one, consider renaming it first.

5. **Regular Exports**: Regularly export important competitions as backups.

## Future Enhancements

Planned improvements for export/import functionality:

1. **File Inclusion**: Include challenge images and files in ZIP exports
2. **Bulk Challenge Import**: Import multiple standalone challenges at once
3. **Partial Import**: Select specific challenges to import from a competition
4. **Import Validation**: Pre-import validation with detailed error reporting
5. **Export History**: Track when and what was exported
6. **Automated Backups**: Schedule automatic competition exports

## Technical Details

### API Endpoints

- `GET /admin/competitions/<id>/export` - Export single competition
- `GET /admin/competitions/export-all` - Export all competitions as ZIP
- `GET /admin/challenges/<id>/export` - Export single challenge
- `GET /admin/competitions/import` - Display import form
- `POST /admin/competitions/import` - Process competition import

### Database Impact

Importing competitions creates new database entries. It does not modify or delete existing data, ensuring safe operation.

### Transaction Safety

Imports are wrapped in database transactions. If any error occurs during import, all changes are rolled back automatically.

## Troubleshooting

### "Invalid JSON file" Error
- Ensure you're uploading a valid JSON file
- Check that the file wasn't corrupted during download
- Try re-exporting the competition

### "Invalid import file format" Error
- The JSON file may be missing required fields
- Ensure you're importing a competition export (not a challenge export)
- Check that the JSON structure matches the expected format

### Import Fails Silently
- Check the application logs for detailed error messages
- Ensure the database has sufficient storage
- Verify that required fields in the JSON are not null

### Challenges Not Appearing
- Check if challenges were imported with `is_active: false`
- Verify the competition was created successfully
- Review application logs for any errors during challenge creation

## Conclusion

The export/import feature provides a powerful tool for managing competitions across different platforms and creating backups. While the current implementation focuses on metadata, it provides a solid foundation for competition migration and archival needs.
