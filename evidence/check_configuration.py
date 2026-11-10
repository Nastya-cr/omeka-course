import os
import pathlib
import subprocess
import tempfile
import yaml
p=pathlib.Path(__file__).resolve().parents[1]
svc={"proxy","omeka","db","monitor","backup"}
for name in ("compose.yaml","stack.yaml"):
    data=yaml.safe_load((p/name).read_text())
    assert data["services"].keys()==svc
    assert {n for n,s in data["services"].items() if "ports" in s}=={"proxy"}
    assert set(data["services"]["omeka"]["networks"])=={"front","back"}
    assert data["services"]["db"]["networks"]==["back"]
    assert data["networks"]["back"]["internal"]
    if name=="stack.yaml":
        assert all(n["driver"]=="overlay" for n in data["networks"].values())
        assert all(v["external"] for v in data["secrets"].values())
    print(f"PASS  {name}: 5 services, 2 networks, only proxy port exposed")
workflow=yaml.load((p/".github/workflows/library.yml").read_text(), Loader=yaml.BaseLoader)
assert workflow["jobs"]["publish"]["needs"]=="smoke"
assert workflow["jobs"]["deploy"]["needs"]=="publish"
assert "workflow_dispatch" in workflow["on"]
assert all("runner." not in value for value in workflow["jobs"]["deploy"]["env"].values())
print("PASS  workflow: smoke, publish, deploy dependencies")
for f in sorted(p.rglob("*.sh")):
    subprocess.run(["sh","-n",str(f)],check=True)
print("PASS  shell syntax: all six scripts")
with tempfile.TemporaryDirectory() as directory:
    d=pathlib.Path(directory).resolve()
    for sub in ("backups","files","bin"):
        (d/sub).mkdir()
    (d/"files/example.txt").write_text("Backup test file\n")
    (d/"secret").write_text("1234567890abcdef")
    stub=d/"bin/mariadb-dump"
    stub.write_text('#!/bin/sh\nprintf "%s\\n" "SELECT 42;"\n')
    stub.chmod(0o755)
    env=dict(os.environ, TMPDIR=str(d), PATH=f'{d/"bin"}:{os.environ["PATH"]}', BACKUP_DIR=str(d/"backups"),
             FILES_DIR=str(d/"files"),DB_SECRET_FILE=str(d/"secret"))
    cmd=["sh",str(p/"scripts/backup.sh")]
    subprocess.run(cmd,env=env,check=True,capture_output=True)
    [backup]=(d/"backups").iterdir()
    subprocess.run(["sha256sum","-c","SHA256SUMS"],cwd=backup,check=True,capture_output=True)
    assert (backup/"database.sql").read_text()=="SELECT 42;\n"
    f=subprocess.check_output(["tar","-xOzf",str(backup/"files.tar.gz"),"./example.txt"],text=True)
    assert f=="Backup test file\n"
    print("PASS  backup: SQL fixture, archived file, both SHA-256 checks")
    stub.write_text('#!/bin/sh\nprintf "%s\\n" "partial"\nexit 2\n')
    fail=subprocess.run(cmd,env=env,capture_output=True)
    assert fail.returncode and list((d/"backups").iterdir())==[backup]
    print("PASS  backup: failed dump leaves no new or partial snapshot")
print("Scope: static checks and shell tests with a stub. Docker execution pending.")
