## zc_common

#### Installation
Add `-e git+http://github.com/zerocater/zc_common.git@0.1.4#egg=zc_common` to your `requirements.txt`

#### Usage

```python
from zc_common import timezone

timezone.now()
```

#### Running tests

You can now run your tests to make sure zc_common code behaves as 
expected. To get started, follow these instructions:
```shell

# Create a new python virtualenv and install dependecies
mkvirtualenv zc_common
workon zc_common
pip install -r requirements

# Run the tests
python runtests.py

```