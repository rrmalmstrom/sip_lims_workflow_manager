# Workflow Templates

This directory contains the master workflow templates for the LIMS Workflow Manager.

## Files

- **`workflow.yml`** - Master workflow template used when creating new projects
  - This is the authoritative template that gets copied to new project directories
  - Protected by Git version control
  - Changes here will affect all new projects created

## Important Notes

⚠️ **Do not modify these templates directly unless you intend to change the workflow for ALL new projects.**

- Template changes are tracked in Git for version control
- The application automatically uses these templates when creating new project workflows
- Existing projects are not affected by template changes

## Template Updates

When updating templates:
1. Test changes thoroughly with a sample project
2. Commit changes to Git with descriptive commit messages
3. Consider backward compatibility with existing projects
4. Update documentation if workflow structure changes significantly