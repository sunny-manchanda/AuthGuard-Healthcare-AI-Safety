# Upload and launch AuthGuard in the existing Colab notebook

Use this route before the project has been pushed to GitHub.

## 1. Prepare the runtime

Open the existing AuthRoute notebook, connect to a GPU, and run only the cells needed to:

1. install/import the model dependencies;
2. mount Drive;
3. load `authroute_lora_v3` or the merged v3 model;
4. define `_model`, `_tokenizer`, `LABEL_TOKENS`, and `classify()`;
5. confirm the seven smoke tests still pass.

Do not run LLaMA Factory training again.

## 2. Upload the project ZIP

```python
from google.colab import files
uploaded = files.upload()  # choose AuthGuard_Starter.zip
```

## 3. Extract and install the interface dependency

```python
!rm -rf /content/AuthGuard
!unzip -q -o /content/AuthGuard_Starter.zip -d /content
!pip -q install "gradio>=4.44,<7"
```

## 4. Connect AuthRoute v3

```python
import sys
sys.path.insert(0, "/content/AuthGuard/src")
sys.path.insert(0, "/content/AuthGuard")

from authguard.router import FineTunedRouter
from authguard.workflow import AuthGuardWorkflow

authguard_workflow = AuthGuardWorkflow.default(
    router=FineTunedRouter(classify)
)

print("Connected AuthGuard to AuthRoute v3")
```

## 5. Run one protected analysis

```python
from authguard.data import load_cases

sample_case = load_cases()[0]
sample_result = authguard_workflow.analyze(sample_case, protected=True)
sample_result.to_dict()
```

## 6. Run the automated attack suite

```python
from authguard.data import load_json
from authguard.evaluation import evaluate_suite, save_results

attacks = load_json("/content/AuthGuard/evals/attack_suite.json")
rows, metrics = evaluate_suite(authguard_workflow, attacks)
save_results(rows, metrics, "/content/AuthGuard/outputs")
metrics
```

## 7. Launch Gradio

```python
from app import build_app

demo = build_app(authguard_workflow)
demo.launch(share=True, debug=False)
```

Keep this final cell running. The `gradio.live` link expires when the Colab runtime or cell stops.

