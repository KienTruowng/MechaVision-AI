# Dua MechaVision AI len GitHub

Kho dich: https://github.com/KienTruowng/MechaVision-AI

## Cach nhanh nhat

Giai nen goi `MechaVision-AI-GitHub-ready.zip` vao o dia, mo **PowerShell** tai thu muc `MechaVision-AI-GitHub-ready` (co thu muc an `.git`). Chay:

```powershell
git remote -v
git push -u origin main
```

Dang nhap GitHub khi duoc yeu cau (Git Credential Manager / trinh duyet). Neu da day thanh cong, tai ma nguon bang:

```powershell
git clone https://github.com/KienTruowng/MechaVision-AI.git
```

## Chay ung dung

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
.\.venv\Scripts\python.exe -m mechavision gui
.\.venv\Scripts\python.exe -m pytest -q
```

Neu may chua co Python 3.12, cai dat truoc. Repo da duoc khoi tao git va commit ma nguon, khong can tao git init / add / commit lan nua. Khoi phuc `.git` khi giai nen. KHONG tai file ZIP len GitHub nhu mot tep zip duy nhat neu muon Codex doc ma nguon.

## Trang thai thuc te

Goi chua co trong so model duoc huan luyen tren dong co LEGO that, va chua kiem chung tu camera va tham chieu doc lap tren may ban. Ket qua demo la mo phong, khong phai ket qua do may that.
