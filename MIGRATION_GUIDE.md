# Conditional Workflow Migration Guide

## Overview
The conditional workflow functionality is fully backward compatible with existing projects. You can update existing projects to use the new conditional features without losing any progress.

## For Existing Projects

### Option 1: Keep Current Workflow (Recommended for Active Projects)
- **No action needed** - Your existing projects will continue to work exactly as before
- The old `allow_skip: true` properties will be ignored but won't cause errors
- You can complete your current projects using the existing linear workflow

### Option 2: Update to Conditional Workflow
If you want to add conditional functionality to an existing project:

1. **Backup your project** (recommended)
2. **Update the project's workflow.yml** by copying the new template:
   ```bash
   cp templates/workflow.yml your_project_folder/workflow.yml
   ```
3. **The system will automatically handle the transition**:
   - Completed steps remain completed
   - Pending steps will now show conditional prompts when appropriate
   - No data or progress is lost

## What Happens When You Update

### If you're before step 9 (second.FA.output.analysis.py):
- Everything continues normally
- When you reach step 9 and complete it, you'll see the new conditional prompt

### If you've already completed step 9:
- The system will automatically detect this
- Step 10 will immediately show the conditional prompt: "Do you want to run a third attempt at library creation?"
- You can choose Yes or No based on your needs

### If you've already completed steps 10-11:
- Those steps will remain marked as completed
- Step 12 will be available to run
- No conditional prompts will appear (since the decision was already made by running the steps)

## State Compatibility

The new system recognizes these existing states:
- `pending` → Works as before
- `completed` → Works as before  
- `skipped` → Works as before (treated as "completed outside workflow")

New states added:
- `awaiting_decision` → Shows Yes/No buttons
- `skipped_conditional` → Shows as "Skipped (conditional)"

## Testing the Update

1. **Make a backup copy** of your project folder
2. **Update the workflow.yml** file
3. **Open the project** in the workflow manager
4. **Verify** that all your completed steps still show as completed
5. **Check** that the next pending step behaves correctly

## Rollback Plan

If you need to rollback:
1. Restore your original `workflow.yml` file from backup
2. The project will work exactly as it did before
3. All progress and data remains intact

## Key Benefits

- ✅ **Zero data loss** - All your work is preserved
- ✅ **Seamless transition** - No manual state adjustments needed
- ✅ **Flexible timing** - Update when convenient for your workflow
- ✅ **Easy rollback** - Can revert if needed
- ✅ **Immediate benefits** - Conditional prompts work right away

## Example Scenarios

### Scenario A: Project at Step 8
- Update workflow.yml → Continue normally → See conditional prompt after completing step 9

### Scenario B: Project completed Step 9
- Update workflow.yml → Immediately see conditional prompt for step 10

### Scenario C: Project completed Steps 10-11
- Update workflow.yml → Step 12 ready to run, no prompts needed

## Support

If you encounter any issues during migration:
1. Check that your `workflow_state.json` file is intact
2. Verify the `workflow.yml` syntax is correct
3. Use the GUI's recovery options if needed
4. Restore from backup if necessary

The system includes comprehensive error handling and recovery mechanisms to ensure smooth transitions.