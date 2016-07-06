## zc_common

#### Installation
Add `zc_common==0.2.0` to your `requirements.txt`

#### Usage

```python
from zc_common import timezone

timezone.now()
```

See the READMEs in submodules for relevant information.

#### Running tests

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