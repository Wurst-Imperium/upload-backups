# Upload Backups Action

GitHub Action for me to upload a copy of every mod I release to my backup server.

## Usage

```yaml
- name: Upload backups
  uses: Wurst-Imperium/upload-backups@v1
  with:
    api_key: ${{ secrets.WI_BACKUPS_API_KEY }}
    project: ExampleMod
    version: 1.0.0
    path: build/libs/*.jar
```

Note: Not for public use. You can't get an API key.
