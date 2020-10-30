# Setup GitHub Repository and tooling

## Pre

Needed:

- [ ] Github account (or organisation and account(s))
- [ ] Codecov account (just choose 'login with github')
- [ ] Travis CI account (again, login with github)
- [ ] Add codecov as an integration from Github's integrations (basically 'buy' it, except its at no cost)

## Configuration

After the initial setup of the repo/initial commit, walk the repo-settings on GitHub using your browser.

- [ ] [Set the product image, turn off wiki and automatically delete branches (from defaults)](https://github.com/plugwise/python-plugwise/settings)
- [ ] [Activate both dependabots and keep dependency graph open](https://github.com/plugwise/python-plugwise/settings/security_analysis)
- [ ] [Webhooks, create one to https://notify.travis-ci.org/](https://github.com/plugwise/Plugwise-Smile/settings/hooks)
- [ ] [Integrations, configure codecov (should show up from organisation)](https://github.com/plugwise/python-plugwise/settings/installations)

For this step you might need to follow [this publishing guide](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/) taking you through most of the steps. Note that the projects on PyPi already [**need to exist**](https://packaging.python.org/tutorials/packaging-projects/) so use a generic token first and later adjust that to only this project (as explained on that howto):

- [ ] [Configure secrets for PYPI_TOKEN and TESTPYPI_TOKEN](https://github.com/plugwise/Plugwise-Smile/settings/secrets)

## Initializing pypi

Once the project is ready for upload to test (i.e. version number ending in `a0` or something likewise): upload it manually using `twine upload`: 

Prepare:

- [ ] `python3.8 -m venv venv ; source venv/bin/activate ; pip install --upgrade pip; pip install -r requirements.txt ; pip install -r requirements_test.txt ; pip install --upgrade setuptools wheel twine`

Package: (**ensure you are in your venv**)

- [ ] [pypi packaging](https://packaging.python.org/tutorials/packaging-projects/)
- [ ] `python3 setup.py sdist bdist_wheel`

Then reconfigure your tokens on the pypi website accordingly (only allowing project updates) and carry on.

**Note** once you complete this you can `pip uninstall setuptools wheel twine` as we are going to keep github and travis do this from now on.

**Important** now go to (test) PyPi and actually invite the other members as owners (or at least maintainers) so everything can live on if yours makes other choices.

## Travis

Go to [travis repositories](https://travis-ci.org/account/repositories) and click on the 'organisations' to view what's in our organisation.

Travis needs the PYPI production token for [PyPI deployment](https://docs.travis-ci.com/user/deployment/pypi/)

Todo: (** ensure you are in your venv**)

- [ ] `gem install travis`
- [ ] Edit '.travis.yml` and make sure it looks like:

```
  user: "__token__"
  password: "pypi-..."
```

- [ ] `travis encrypt {TOKENHERE} --add deploy.password`

## Test

Now test by creating a branch `git branch -a test` and committing/pushing against this and see if everything starts to work.
(Mostly just click on the build details and figure out what/if travis is doing everything its supposed to do and is 'green'.

If it is, merge, and it should do the real thing (assuming you increased the version number correctly).

## Connect codecov

Codecov can take a while on a new repo, but just check to see if it sees all repo's you have (might not see the newest ones yet).

From [integrations](https://github.com/plugwise/python-plugwise/settings/installations) set to configure codecov

## Templates for Github issues

If you push templates within the `.github/ISSUE_TEMPLATES` directory they should be available, if not:

- [ ] Go to [issue templates](https://github.com/plugwise/python-plugwise/issues/templates/edit) and create them


