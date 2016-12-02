## zc_common

### Installation
`pip install zc_common`

### Usage

```python
from zc_common import timezone

timezone.now()
```

See the READMEs in submodules for relevant information.

### Deploying new versions

#### Prerequisite

Before you can deploy new versions, you'll need to add PyPi credentials to your machine so that `twine` works.

First, `pip install twine`.

Then, create a file at `~/.pypirc` with the following contents:
```
[distutils]
index-servers =
    pypi
    pypitest


[pypi]
repository: https://pypi.python.org/pypi
username: zerocater
password: <GET FROM LASTPASS "PyPi Live">

[pypitest]
repository: https://testpypi.python.org/pypi
username: zerocater
password: <GET FROM LASTPASS "PyPi Test">
```

You'll need to get 2 passwords from Lastpass and insert them into the file. Once that file has been created, you'll be able to upload new releases to PyPi.

#### Deployment

1. Bump the version number in `setup.py` in both the `version` and the `download_url`
2. Make sure all desired code is committed and merged into master, **including the setup.py changes**
3. Create a [release](https://github.com/ZeroCater/zc_common/releases) for the new version. This creates the download URL specified in step 1
4. `./release.sh` This will create the release file and ask if you want to upload it to PyPi
5. You should now be able to `pip install` the new version

### Running tests

You can now run your tests to make sure zc_common code behaves as 
expected. To get started, follow these instructions:
```shell

# Create a new python virtualenv and install dependencies
mkvirtualenv zc_common
workon zc_common
pip install -r requirements

# Run the tests
python runtests.py
```
