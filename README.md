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

app = create_app("local.py")
db.create_all(app=app)

with app.test_request_context():
    [db.session.add(Category(c.strip())) for c in open("categories.txt")]
    db.session.commit()
```
