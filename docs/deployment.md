# Deployment Layout

部署相关文件统一放在 `deployments/`：

- `deployments/docker`: Dockerfile
- `deployments/k8s`: Kubernetes YAML
- `deployments/scripts`: 部署与运维脚本

镜像默认入口：

- Master: `python -m apps.master.main`
- Worker: `python -m apps.worker.main`

运行配置位于 `configs/application.yml`。
