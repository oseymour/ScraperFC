=========================
Contributing to ScraperFC
=========================

One of the best ways to give back is to contribute code to ScraperFC! These instructions are a work
in progress so if you attempt to follow them and run into issues please reach out. If you have 
questions about ANY of this, the best way to get help is to join our 
`Discord <https://discord.com/invite/C5N8dqCJAq>`_ and ask. I will also update this page as needed.

1. Forking and cloning
----------------------
The first step is to get a working copy of the latest code on your machine. Fork the repository from
the latest commit on the "main" branch and then clone your fork locally. I'm not going to go into 
details on this here because there are a ton of tutorials for this on the internet.

2. Test package management tools
---------------------------------
In v3.0.0 I added several package mangement tools to help maintain the package. We're now going to 
run these to make sure everything is working before making any changes.

2.1 Tox
^^^^^^^
The tool for running the various package management tasks is 
`Tox <https://tox.wiki/en/latest/index.html>`_. Install it.

Inside the repo you forked and cloned, there is a ``pyproject.toml`` file. This is ScraperFC's config 
file and at the bottom there is a ``[tool.tox]`` section that configures Tox. If you want to 
understand the nitty gritty of all of this feel free to dig into the Tox docs. I'll just cover the 
high level details here.

To test each of the Tox environments, run the following commands from the package root and make 
sure they all pass.

* Test suite: ``tox -r``
* Build docs: ``tox -r -e docs``
* Build distributables: ``tox -r -e build``
* Code linter: ``tox -r -e lint``
* Typecheck: ``tox -r -e typecheck``

3. Make your changes
--------------------
Now that we know the current code works, go ahead and make whatever changes you were going to make.

Please make sure that any code you added is covered by the test suite, especially if you're adding 
new functions or capability. If you're fixing already existing code to address a bug, it's probably 
already covered.

Also, please make sure you update the docstrings and docs files as necessary based on your changes. 
Changes to the code without appropriate docstring changes will not be accepted until the docstrings 
have been updated.

4. Re-run package management tools
----------------------------------
After making your changes, re-run all of the package management tools and confirm that they all 
pass.

5. Open a Pull Request
----------------------
At this point, please open a pull request (PR) to merge your forked code back into the project. 
I've set up GitHub actions to run all of the package management tools mentioned above. When these 
run and pass, I'll review the PR. If I don't have any additional changes that need to be made, I'll 
accept the PR.

If you're fixing an open issue, please make sure you mention the issue in the PR.
