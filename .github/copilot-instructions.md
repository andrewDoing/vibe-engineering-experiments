<rules>
    <notify>
    When you are done, use the #tool:show-notification tool to notify the user that you have completed the task.
    
    Set `sound` to `true`
    </notify>

    <planned_work>
    When you are told to "work" on a task, you should:
    1. Find the first task in the plan file that is not marked as complete.
    2. Read the task description and any relevant context.
    3. Complete the task as described in the plan file.
    4. After completing the task, mark it as complete in the plan file.

    At the VERY END of a conversation where edits are made to files and ALL changes to files are done:
    
    1. Stage all changes
    2. Commit the changes along with a short summary of the changes you made, and a bulleted list of the changes made by file.
    </planned_work>

    <context>
    If you lack context on how to solve the user's request:
    
    FIRST, use #tool:resolve-library-id from Context7 to find the referenced library.

    NEXT, use #tool:get-library-docs from Context7 to get the library's documentation to assist in the user's request.
    </context>
</rules>