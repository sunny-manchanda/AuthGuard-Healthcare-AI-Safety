# Connect AuthGuard to the existing AuthRoute v3 notebook

Do not run the training cells again. Start after the existing cell that defines `classify(message_text)` and confirms the v3 smoke test.

## Option A — after the AuthGuard folder is pushed to GitHub

```python
%cd /content
!git clone YOUR_AUTHGUARD_REPOSITORY_URL AuthGuard
%cd /content/AuthGuard
!pip -q install -r requirements.txt
```

## Connect the fine-tuned predictor

```python
import sys
sys.path.insert(0, "/content/AuthGuard/src")

from authguard.router import FineTunedRouter
from authguard.workflow import AuthGuardWorkflow

authguard_workflow = AuthGuardWorkflow.default(
    router=FineTunedRouter(classify)
)

print("AuthGuard is connected to AuthRoute v3")
```

## Verify one protected case

```python
from authguard.data import load_cases

case = load_cases()[0]
result = authguard_workflow.analyze(case, protected=True)
result.to_dict()
```

## Launch the full interface

```python
from app import build_app

demo = build_app(authguard_workflow)
demo.launch(share=True, debug=False)
```

The generated `gradio.live` address is temporary. Keep the Colab cell running while demonstrating the application.

