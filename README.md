```
pip install -r requirements.txt
```

```
GOOGLE_OAUTH2_CLIENT_ID = "<your client ID>"
GOOGLE_OAUTH2_CLIENT_SECRET = "<your client secret>"
```

```
from arxiv import create_app
from arxiv.database import db
from arxiv.models import *

db.create_all(app=create_app("local.py"))
```
