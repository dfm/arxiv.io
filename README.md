```
pip install -r requirements.txt
```

```
GOOGLE_OAUTH2_CLIENT_ID = "<your client ID>"
GOOGLE_OAUTH2_CLIENT_SECRET = "<your client secret>"
```

```
from ugly import create_app
from ugly.database import db
from ugly.models import *

db.create_all(app=create_app("local.py"))
```
