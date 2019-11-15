## Development

### Prerequisites

- [Git](https://git-scm.com/)

### Contributions of OEP website
### Workflow

The development of a feature for this repository is inspired from the workflow described 
by [Vincent Driessen](https://nvie.com/posts/a-successful-git-branching-model/):

1. Create [an issue](https://help.github.com/en/articles/creating-an-issue) on the github repository
    
    Discussion about the implementation details should occur within this issue.
    
2. Checkout `develop` and pull the latest changes
    ```bash
    git checkout develop
    ```
    ```bash
    git pull
    ```
3. Create a branch from `develop` to work on your issue (see below, the "Branch name convention" section)
    ```bash
    git checkout -b feature/myfeature
    ```
4. Push your local branch on the remote server `origin`
    ```bash
    git push
    ```
    If your branch does not exist on the remote server yet, git will provide you with instructions, simply follow them
5. Submit a pull request (PR)
    - Follow the [steps](https://help.github.com/en/articles/creating-a-pull-request) of the github help to create the PR.
    - Please note that you PR should be directed from your branch (for example `myfeature`) towards the branch `develop`
6. Describe briefly (i.e. in one or two lines) what you changed in the `CHANGELOG.md` file. End the description by the number in parenthesis `(#<your PR number>)`
7. Commit the changes to the `CHANGELOG.md` file
8. Write the PR number in the corresponding issue so that they are linked. Write it with one of the [special keywords](https://help.github.com/en/github/managing-your-work-on-github/closing-issues-using-keywords) so that the issue will be automatically closed when the PR is merged (example: `Closes #<your issue number>`)
9. [Ask](https://help.github.com/en/github/managing-your-work-on-github/assigning-issues-and-pull-requests-to-other-github-users) for review of your PR 

10. Check that, after this whole process, you branch does not have conflict with `develop` (github prevents you to merge if there are conflicts). In case of conflicts you are responsible to fix them on your branch before your merge (see below "Fixing merge conflicts" section)
    
11. (if approved) Merge the PR into `develop` and delete the branch on which you were working. In the merge message on github, you can notify people who are currently working on other branches that you just merged into `develop`, so they know they have to check for potential conflicts with `develop`
   

### Fixing merge conflicts


Avoid large merge conflict by merging the updated `develop` versions in your branch.

In case of conflicts between your branch and `develop` you must solve them locally.

1. Get the latest version of `develop`
    ```bash
    git checkout develop
    ```
   
    ```bash
    git pull
    ```
    
2. Switch to your branch

    ```bash
    git checkout <your branch>
    ```
    
3. Merge `develop` into your branch
    ```bash
    git merge develop
    ```
    
4. The conflicts have to be [manually](https://help.github.com/en/github/collaborating-with-issues-and-pull-requests/resolving-a-merge-conflict-using-the-command-line) resolved
    


### Branch name convention
The convention is to always have `feature/` in the branch name. The `myfeature` part should describe shortly what the feature is about (separate words with `_`).

Try to follow [these conventions](https://chris.beams.io/posts/git-commit) for commit messages:
- Keep the subject line [short](https://chris.beams.io/posts/git-commit/#limit-50) (i.e. do not commit more than a few changes at the time)
- Use [imperative](https://chris.beams.io/posts/git-commit/#imperative) for commit messages 
- Do not end the commit message with a [period](https://chris.beams.io/posts/git-commit/#end) 
You can use 
```bash
git commit --amend
```
to edit the commit message of your latest commit (provided it is not already pushed on the remote server).
With `--amend` you can even add/modify changes to the commit.
