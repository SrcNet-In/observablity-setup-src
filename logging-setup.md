# 🛠️ Observability Setup with Loki & Alloy in Kubernetes

This guide walks you through deploying **Grafana Loki** for log aggregation and **Grafana Alloy** for log collection in Kubernetes. Assuming **Grafana** is already installed and accessible.

---

## 🧰 Tools Used

- **Grafana Loki**: A log aggregation system tailored for Kubernetes.
- **Grafana Alloy**: A lightweight, flexible collector for logs, metrics, and traces.
- **Grafana**: For visualizing logs using Loki as a data source.

---

## 🚀 Loki Installation (Monolithic Mode)

We'll install Loki in **monolithic mode** for this example, which is simpler and ideal for small to medium clusters. 

### 1. Create Namespace

```bash
kubectl create namespace monitoring
```

### 2. Add Grafana Helm Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### 3. Get Loki Default Values

```bash
helm show values grafana/loki > values.yaml
```

### 4. Edit `values.yaml` for Monolithic Deployment

```yaml
loki:
  auth_enabled: false
  commonConfig:
    replication_factor: 1
  schemaConfig:
    configs:
      - from: "2025-04-01"
        store: tsdb
        object_store: s3
        schema: v13
        index:
          prefix: loki_index_
          period: 24h
  pattern_ingester:
      enabled: true
  limits_config:
    allow_structured_metadata: true
    volume_enabled: true
  ruler:
    enable_api: true

minio:
  enabled: true

deploymentMode: SingleBinary

singleBinary:
  replicas: 1

backend:
  replicas: 0
read:
  replicas: 0
write:
  replicas: 0
ingester:
  replicas: 0
querier:
  replicas: 0
queryFrontend:
  replicas: 0
queryScheduler:
  replicas: 0
distributor:
  replicas: 0
compactor:
  replicas: 0
indexGateway:
  replicas: 0
bloomCompactor:
  replicas: 0
bloomGateway:
  replicas: 0
```

### 5. Install Loki

```bash
helm install loki grafana/loki -n monitoring -f values.yaml
```

---

## 🏗️ Loki Deployment Modes

Loki supports three modes:

1. **Monolithic (SingleBinary)**: All components run in a single process. Best for dev/staging/small prod.
2. **Simple Scalable**: Components like ingester, querier, etc., are split out but share a single process per replica.
3. **Microservices Mode**: Full separation of components (e.g., distributor, ingester, querier). Ideal for large-scale clusters.

| Feature                      | **Monolithic (SingleBinary)**                   | **Simple Scalable**                          | **Microservices Mode**                          |
|------------------------------|-------------------------------------------------|---------------------------------------------|-------------------------------------------------|
| **Description**               | All components run as a single binary process.   | Components like ingester, querier, etc. are separated into individual components but still share a single process per replica. | Full separation of components (e.g., distributor, ingester, querier). Each component runs as a separate service. |
| **Ideal Use Case**            | Small to medium clusters, development, or staging environments. | Medium-scale clusters with moderate scalability needs. | Large-scale, high-traffic environments with high availability needs. |
| **Scalability**               | Limited scalability (all components are together in a single process). | Can scale individual components (e.g., querier, ingester) independently. | Highly scalable, full independent scaling of each component. |
| **Operational Complexity**    | Low, easy to deploy and manage.                  | Moderate, needs separate management for individual components. | High, each component must be managed and scaled independently. |
| **Fault Tolerance**           | Single point of failure (if the binary fails, everything fails). | Better fault tolerance than monolithic (individual components can fail without taking down the entire system). | High fault tolerance, as failure in one component does not affect others. |
| **Resource Efficiency**       | More resource-efficient as it uses a single process. | More resource-intensive as individual components run in separate processes. | Most resource-intensive, as each component has its own resources and scaling. |
| **Ideal For**                 | Small-scale setups, testing, or development environments. | Medium-scale setups requiring some scalability but avoiding full microservices complexity. | Large-scale production environments requiring high resilience, scalability, and fault tolerance. |

For more details on deployment modes, [see the Loki deployment modes documentation](https://grafana.com/docs/loki/latest/get-started/deployment-modes/).

---

## 🪣 Storage & Retention

Loki can use object storage like:

- **Amazon S3**
- **Google Cloud Storage (GCS)**
- **Azure Blob**

> **Compression**: Loki **automatically compresses logs using Snappy** before storing them in object storage.

---

## ⚙️ Configure Alloy for Log Collection

### 1. Download Default Alloy Values

```bash
helm show values grafana/alloy > values.yaml
```

### 2. Edit `values.yaml` for Alloy Configuration

![Alloy configuration graph](./images/image_3.png)

```yaml
alloy:
  configMap:
    content: |-
      loki.write "default" {
        endpoint {
          url = "http://loki.monitoring:3100/loki/api/v1/push"
        }
      }

      discovery.kubernetes "pod" {
        role = "pod"
      }

      discovery.relabel "pod_logs" {
        targets = discovery.kubernetes.pod.targets

        rule {
          source_labels = ["__meta_kubernetes_namespace"]
          action        = "replace"
          target_label  = "namespace"
        }

        rule {
          source_labels = ["__meta_kubernetes_pod_name"]
          action        = "replace"
          target_label  = "pod"
        }

        rule {
          source_labels = ["__meta_kubernetes_pod_container_name"]
          action        = "replace"
          target_label  = "container"
        }

        rule {
          source_labels = ["__meta_kubernetes_namespace", "__meta_kubernetes_pod_container_name"]
          action        = "replace"
          target_label  = "job"
          separator     = "/"
          replacement   = "$1/$2"
        }

        rule {
          source_labels = ["__meta_kubernetes_pod_uid", "__meta_kubernetes_pod_container_name"]
          action        = "replace"
          target_label  = "__path__"
          separator     = "/"
          replacement   = "/var/log/pods/*$1/*.log"
        }
      }

      loki.source.kubernetes "pod_logs" {
        targets    = discovery.relabel.pod_logs.output
        forward_to = [loki.process.pod_logs.receiver]
      }

      loki.process "pod_logs" {
        stage.static_labels {
          values = {
            cluster = "kubernetes"
          }
        }
        forward_to = [loki.write.default.receiver]
      }
```
---

## 📦 Install Alloy with Helm

```bash
helm install alloy grafana/alloy -n monitoring -f values.yaml
```

---

## 📊 Add Loki as a Data Source in Grafana

1. Open **Grafana → Connections → Data Sources → Add Data Source**.
2. Choose **Loki**.
3. URL: `http://loki.monitoring.svc.cluster.local:3100`
4. Click **Save & Test**.

You can now explore logs under **Explore → Logs**.

---

## 📚 References

- [Loki Docs](https://grafana.com/docs/loki/latest/)
- [Alloy Docs](https://grafana.com/docs/alloy/latest/)
- [Loki Deployment Modes](https://grafana.com/docs/loki/latest/get-started/deployment-modes/)
- [Loki Deployment Guides](https://grafana.com/docs/loki/latest/setup/install/helm/)
- [Loki Architecture](https://grafana.com/docs/loki/latest/get-started/architecture/)
