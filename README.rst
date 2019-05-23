GitDrop
=======

Tasty sweety git goodness, Or filesharing made with with git.


Aim
---

GitDrop is an implementation of a version control shared directory aim
at non developers with a bit savvy.  The application allow use to 
use a remote git repo hosting site as shared file site for collaborative
projects.

Git Drop uses i-notify to watch for file changes and commits all the 
(non-ignored) changes made to the repo after a small delay and pushes 
immediately. After each push a pull is done, and test merge is carried out
to look for conflicts, if the merge is successful then it is made active and
the use is moved on to the merged head, if not pull synchronization is disabled
until a successful is manually performed.

Later versions will aid the user in launching appropriate mergetools.
