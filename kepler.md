# Kepler: Kubernetes-based Efficient Power Level Exporter

---

## What is Kepler?

**Kepler** stands for **Kubernetes-based Efficient Power Level Exporter**. It is an open-source project designed to estimate and monitor the energy consumption and CO₂ emissions of workloads running within Kubernetes clusters. 
By leveraging various data sources and machine learning models, Kepler shows detailed power usage for each container and pod.

---

## How Kepler Works

### Data Collection Methods

Kepler employs multiple approaches to gather power-related data:

1. **eBPF (Extended Berkeley Packet Filter)**: Utilizes eBPF programs to monitor performance counters and other system stats, providing detailed insights into resource utilization at the process level.

2. **Hardware Counters**:  
   - **CPU and DRAM Power**:  
     - Accesses Intel Running Average Power Limit (RAPL) metrics to measure power consumption for both CPU and DRAM.  
   - **GPU Power**:  
     - Leverages NVIDIA Management Library (NVML) to retrieve power usage data for GPUs.  
   - **SPECPower-based Estimates**:  
     - Uses SPECPower benchmarks to estimate power consumption based on system performance.  
   - **Hardware Monitor Sensors**:  
     - Gathers data from various hardware sensors to monitor power usage across different components (e.g., temperature, voltage, and fan speed).

3. **Platform Power Meters**:  
   - Built into the CPU or system-on-chip (SoC) to measure the overall power consumption of the system.  
   - Collects power consumption data via system-level interfaces:  
     - **Advanced Configuration and Power Interface (ACPI)**: Monitors system-wide power states, such as the total power used by the CPU, memory, and other components.  
     - **Intelligent Platform Management Interface (IPMI)**: Provides overall power consumption metrics for the entire platform.

4. **Trained Power Models**: In scenarios where real-time power metrics are unavailable, Kepler employs regression-based machine learning models trained on benchmark data to estimate power consumption.

These diverse data sources enable Kepler to provide accurate energy consumption metrics across various environments.

---

## Understanding eBPF

**eBPF** (Extended Berkeley Packet Filter) is a technology that allows programs to run in the kernel space of an operating system without modifying the kernel itself. 
It enables safe and efficient monitoring and manipulation of kernel behavior. 
eBPF programs are attached to various hooks in the kernel, such as system calls, tracepoints, and network events. 
When these events occur, the eBPF programs are triggered to execute.

In the context of Kepler, eBPF is used to collect fine-grained power consumption metrics by accessing hardware performance counters and other system statistics. This enables accurate estimation of energy usage at the container level.

---
### Kepler Architecture 

![Kepler Architecture](./images/kepler-arch.png)

*Source: [https://sustainable-computing.io/design/architecture/](https://sustainable-computing.io/design/architecture/)*

---

## 🛠️ Installation in Kubernetes

### High Privilege Mode

In high privilege mode, Kepler utilizes eBPF to gather detailed power consumption metrics. This requires elevated privileges to load and execute eBPF programs within the kernel.

**Installation Steps**:

1. **Install Prometheus Stack** (if Prometheus isn't already installed):

   ```bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   helm install prometheus prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace --wait
   ```

2. **Install Kepler**:

   ```bash
   helm repo add kepler https://sustainable-computing-io.github.io/kepler-helm-chart
   helm repo update
   helm install kepler kepler/kepler \
     --namespace monitoring \
     --set serviceMonitor.enabled=true \
     --set serviceMonitor.labels.release=prometheus \
     --set securityContext.runAsUser=0 \
     --set securityContext.runAsGroup=0 \
     --set securityContext.fsGroup=0 \
     --set securityContext.capabilities.add[0]=CAP_BPF \
     --set securityContext.capabilities.add[1]=CAP_NET_ADMIN \
     --set securityContext.capabilities.add[2]=CAP_SYS_ADMIN
   ```

3. **Verify Installation**:

   ```bash
   kubectl get pods -n monitoring
   ```

4. **Integrate with Grafana**:

   - Import Kepler dashboard JSON into Grafana.
   - Refresh the browser window to load the new dashboard.

### Low Privilege Mode

In low privilege mode, Kepler operates with reduced functionality due to limited access to eBPF and kernel resources. It relies on alternative methods, such as trained power models, to estimate power consumption.

**Installation Steps**:

1. **Install Kepler**:

   ```bash
   helm repo add kepler https://sustainable-computing-io.github.io/kepler-helm-chart
   helm repo update
   helm install kepler kepler/kepler \
     --namespace monitoring \
     --set serviceMonitor.enabled=true \
     --set serviceMonitor.labels.release=prometheus \
     --set securityContext.runAsUser=1000 \
     --set securityContext.runAsGroup=1000 \
     --set securityContext.fsGroup=1000 \
     --set securityContext.capabilities.drop[0]=ALL 
   ```

3. **Verify Installation**:

   ```bash
   kubectl get pods -n monitoring
   ```

4. **Integrate with Grafana**:

   - Import Kepler dashboard JSON into Grafana.
   - Refresh the browser window to load the new dashboard..

---

### Capabilities in Kepler

Kepler utilizes specific Linux capabilities to access system-level resources for accurate power consumption monitoring. These capabilities enable Kepler to gather detailed metrics, such as CPU and memory usage, and to interact with hardware components like GPUs.

| Capability       | Role in Kepler's Functionality                             |
|------------------|------------------------------------------------------------|
| `CAP_BPF`        | Enables eBPF-based performance monitoring                  |
| `CAP_NET_ADMIN`  | Allows network-related power consumption monitoring        |
| `CAP_SYS_ADMIN`  | Grants access to hardware-level power metrics and GPU data |

---

## Accuracy Comparison

| Step                     | High Privilege Mode                             | Low Privilege Mode                                  |
|--------------------------|-------------------------------------------------|-----------------------------------------------------|
| **eBPF Access**          | Full access                                     | Limited or none                                     |
| **Kernel Headers**       | Required                                        | Not required                                        |
| **Container Capabilities** | `CAP_BPF`, `CAP_NET_ADMIN`, `CAP_SYS_ADMIN`    | Limited capabilities                                |
| **Power Estimation**     | Accurate using eBPF                            | Estimated using alternative methods                 |
| **Grafana Integration**  | Full integration with detailed metrics          | Limited integration with basic metrics              |

---

## References

- [Kepler GitHub Repository](https://github.com/sustainable-computing-io/kepler)
- [Kepler Installation Guide](https://sustainable-computing.io/installation/kepler-helm/)
- [Kepler Deep Dive](https://sustainable-computing.io/usage/deep_dive/)
- [Kepler on CNCF](https://www.cncf.io/projects/kepler/)
- [Kepler Architecture Overview](https://www.cncf.io/blog/2023/10/11/exploring-keplers-potentials-unveiling-cloud-application-power-consumption/)
- [eBPF Wikipedia](https://en.wikipedia.org/wiki/EBPF)
