# Workflow Templates

This directory contains the master workflow templates for the LIMS Workflow Manager.

## Files

- **`sip_workflow.yml`** - SIP (Stable Isotope Probing) workflow template for 21-step comprehensive fractionation workflow
- **`sps_workflow.yml`** - SPS-CE (Single Particle Sorts & Cell Enrichments) workflow template for 6-step focused library creation workflow
- **`CapsuleSorting_workflow.yml`** - Capsule Sorting workflow template for 6-step capsule sorting and preparation workflow

These are the authoritative templates that get copied to new project directories:
- Protected by Git version control
- Changes here will affect all new projects created
- Each workflow type has its own specific template with appropriate step configurations

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

## Conditional Workflow Features

The current template includes conditional workflow functionality:

- **Step 10 (Third Attempt Library Creation)**: Conditional step triggered after `second.FA.output.analysis.py` completion
  - Presents Yes/No decision prompt to users
  - "Yes" proceeds to emergency third attempt workflow
  - "No" skips directly to final analysis step
- **Step 11 (Emergency Third FA Output Analysis)**: Dependent on step 10 decision
  - Only becomes available if user chooses "Yes" for step 10
  - Automatically skipped if user chooses "No" for step 10

### Conditional Configuration Structure

```yaml
conditional:
  trigger_script: "script_name.py"  # Script completion that triggers the decision
  prompt: "Question text"           # Question presented to user
  target_step: "step_name"         # Step to activate on "No" decision
  depends_on: "decision_id"        # For dependent steps
```

This system maintains full backward compatibility - existing projects without conditional configuration continue to work normally.