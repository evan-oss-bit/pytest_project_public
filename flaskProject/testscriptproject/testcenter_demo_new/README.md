# testcenter_demo_new

This is a bundled pytest script project for PyTestTool.

It demonstrates:

- pytest project structure under `flaskProject/testscriptproject`
- `pytest.ini` and `data.ini` configuration files
- shared fixtures in `conftest.py`
- common helper modules
- normal test cases, parametrized cases, shared token examples, and log output
- mixed pass/fail results for report preview and failure trend testing

Use it from PyTestTool:

1. Start the backend and frontend.
2. Open `脚本项目列表`.
3. Click `全部项目列表`.
4. Find `testcenter_demo_new` and create it as a script project.
5. Use `扫描/同步脚本` to import pytest cases.
6. Create a test set or run the synchronized cases to view reports.

The project intentionally contains several failing assertions so new users can see failed case reports, logs, and trend data.
