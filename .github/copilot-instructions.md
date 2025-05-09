<rules>
    <notify>
    When you are done, use the #tool:show-notification tool to notify the user that you have completed the task.
    
    Set `sound` to `true`
    </notify>

    <edit_file>
    At the VERY END of a conversation where edits are made to files and ALL changes to files are done:
    
    1. Double check that you're done making changes
    2. Stage all changes
    3. Commit the changes along with a short summary of the changes you made, and a bulleted list of the changes made by file.
    </edit_file>

    <context>
    If you lack context on how to solve the user's request:
    
    FIRST, use #tool:resolve-library-id from Context7 to find the referenced library.

    NEXT, use #tool:get-library-docs from Context7 to get the library's documentation to assist in the user's request.
    </context>
</rules>