## 📦 FLIR Spinnaker SDK 설치 (Ubuntu 20.04, ARM64 / Jetson)

### ✅ 준비물
아래 두 파일이 `install_files/` 폴더에 존재해야 합니다.


---

### 1. Spinnaker SDK 설치

```bash
cd install_files/

# 압축 해제
tar -xzf spinnaker-4.2.0.88-arm64-20.04-pkg.tar.gz
cd spinnaker-4.2.0.88-arm64

# 설치(관리자 권한 필요)
sudo ./install_spinnaker.sh

spinview &
```

### 2. Python Bindings 설치 (Python API)

Python 3.8 / aarch64 환경 기준

```bash
tar -xzf spinnaker_python-4.2.0.88-cp38-cp38-linux_aarch64.tar.gz
cd spinnaker_python-4.2.0.88-cp38-cp38-linux_aarch64
sudo python3 setup.py install
```

설치 확인
```bash
python3 - <<EOF
import PySpin
print("PySpin version:", PySpin.__version__)
EOF
```